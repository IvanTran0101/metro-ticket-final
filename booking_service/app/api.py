from email.policy import default
import uuid
import random
import string
import json
import redis 
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import text
from sqlalchemy.orm import Session
from booking_service.app.settings import settings
from booking_service.app.db import get_db
from booking_service.app.schemas import (
    BookingCreateRequest,
    BookingResponse,
    BookingUpdateRequest,
    BookingCancelRequest
)

from booking_service.app.clients.scheduler_client import SchedulerClient

router = APIRouter()
r = redis.Redis.from_url(settings.REDIS_URL, decode_responses= True)

@router.post("/booking/post/trip_confirm", response_model=BookingResponse)
def create_booking(
    req: BookingCreateRequest,
    idempotency_key: str| None = Header(default= None, alias="Idempotency-Key"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db)
):
    if idempotency_key:
        cache_key = f"idempotency:{idempotency_key}"
        cached_data = r.get(cache_key)
        if cached_data:
            print(f"Idempotency hit:{idempotency_key}")
            return BookingResponse(**json.loads(cached_data))

    MAX_PENDING_BOOKINGS = 2    
    MAX_PENDING_SEATS = 10        
    TIMEOUT_MINUTES = 5

    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user context")
    
    sql_check = text("""
        SELECT COUNT(*) AS pending_count
        FROM bookings
        WHERE user_id = :uid AND status = 'Pending' AND created_at > NOW() - INTERVAL '5 minutes'
    """)

    pending_count = db.execute(sql_check, {"uid": x_user_id}).scalar()

    if  req.seats_reserved > MAX_PENDING_SEATS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="You booked too many seats.")

    if pending_count >= MAX_PENDING_BOOKINGS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="You already have 2 pending bookings. Please wait {TIMEOUT_MINUTES} minutes before creating a new one.")
    
    booking_id = str(uuid.uuid4())
    booking_code = "".join(random.choices(string.ascii_uppercase + string.digits, k = 6))

    scheduler_client = SchedulerClient()

    try:
        trip_info = scheduler_client.get_trip(req.trip_id)
        seat_fare = float(trip_info["fare_per_seat"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Trip ID")

    total_amount = seat_fare * req.seats_reserved

    try:
        scheduler_client.lock_seat(req.trip_id, booking_id, req.seats_reserved)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not reserve seat")
    

    sql = text(
             """
            INSERT INTO bookings (
                booking_id, trip_id, user_id, seats, seat_fare, 
                total_amount, status, booking_code, created_at
            )
            VALUES (
                :bid, :tid, :uid, :seats, :fare, 
                :total, 'Pending', :code, :time
            )
            RETURNING created_at
        """
        )

    params = {
            "bid": booking_id,
            "tid": req.trip_id,
            "uid": x_user_id,
            "seats": req.seats_reserved,
            "fare": seat_fare,
            "total": total_amount,
            "code": booking_code,
            "time": datetime.now(timezone.utc),
        }

    row = db.execute(sql,params).mappings().first()
    db.commit()
    response= BookingResponse(
        booking_id=booking_id,
        trip_id=req.trip_id,
        user_id=x_user_id,
        seats=req.seats_reserved,
        seat_fare=seat_fare,
        total_amount=total_amount,
        status="Pending",
        booking_code=booking_code,
        created_at=row["created_at"].replace(tzinfo=timezone.utc),
    )
    if idempotency_key:
        cache_key = f"idempotency:{idempotency_key}"
        r.setex(cache_key, 86400, response.json())
    return response

@router.get("/get/booking/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: str, db: Session = Depends(get_db)):
    sql = text("SELECT * FROM bookings WHERE booking_id = :bid")
    row = db.execute(sql, {"bid": booking_id}).mappings().first()
    
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
        
    return BookingResponse(
        booking_id=str(row["booking_id"]),
        trip_id=str(row["trip_id"]),
        user_id=str(row["user_id"]),
        seats=row["seats"],
        seat_fare=row["seat_fare"],
        total_amount=row["total_amount"],
        status=row["status"],
        booking_code=row["booking_code"],
        created_at=row["created_at"].replace(tzinfo=timezone.utc),
        paid_at=row["paid_at"].replace(tzinfo=timezone.utc) if row["paid_at"] else None,
        cancelled_at=row["cancelled_at"].replace(tzinfo=timezone.utc) if row["cancelled_at"] else None,
    )
@router.post("/internal/post/booking/booking_update")
def update_booking_status(
    booking_id: str, 
    req: BookingUpdateRequest, 
    db: Session = Depends(get_db)
):
    """
    Called by Payment Service to update status (e.g. to 'Paid').
    """
    sql = text(
        """
        UPDATE bookings 
        SET status = :status, paid_at = CASE WHEN :status = 'Paid' THEN NOW() ELSE paid_at END
        WHERE booking_id = :bid
        RETURNING booking_id
        """
    )
    result = db.execute(sql, {"status": req.status, "bid": booking_id})
    db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
        
    return {"ok": True}

@router.post("/internal/post/booking/booking_unlock")
def unlock_booking(booking_id: str, db: Session = Depends(get_db)):
    sql = text(
        """
        UPDATE bookings
        SET status = 'Cancelled', cancelled_at = NOW()
        WHERE booking_id = :bid
        RETURNING trip_id
        """
    )
    row = db.execute(sql, {"bid": booking_id}).mappings().first()
    db.commit()

    if not row:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    return {"trip_id": row["trip_id"]}

@router.post("/booking/post/cancel", response_model=BookingResponse)
def cancel_user_booking(
    req: BookingCancelRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db)
):
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user context")

    sql_check = text("SELECT * FROM bookings WHERE booking_id = :bid AND user_id = :uid")
    booking = db.execute(sql_check, {"bid": req.booking_id, "uid": x_user_id}).mappings().first()

    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found or access denied")

    if booking["status"] == "Cancelled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking is already cancelled")

    scheduler_client = SchedulerClient()
    try:
        scheduler_client.seat_canceled(booking["trip_id"], req.booking_id) 
    except Exception as e:
        print(f"Warning: Failed to unlock seats in scheduler: {e}")

    sql_update = text(
        """
        UPDATE bookings
        SET status = 'Cancelled', cancelled_at = NOW()
        WHERE booking_id = :bid
        RETURNING *
        """
    )
    
    updated_row = db.execute(sql_update, {"bid": req.booking_id}).mappings().first()
    db.commit()

    return BookingResponse(
        booking_id=str(updated_row["booking_id"]),
        trip_id=str(updated_row["trip_id"]),
        user_id=str(updated_row["user_id"]),
        seats=updated_row["seats"],
        seat_fare=updated_row["seat_fare"],
        total_amount=updated_row["total_amount"],
        status=updated_row["status"],
        booking_code=updated_row["booking_code"],
        created_at=updated_row["created_at"].replace(tzinfo=timezone.utc),
        paid_at=updated_row["paid_at"].replace(tzinfo=timezone.utc) if updated_row["paid_at"] else None,
        cancelled_at=updated_row["cancelled_at"].replace(tzinfo=timezone.utc) if updated_row["cancelled_at"] else None,
    )