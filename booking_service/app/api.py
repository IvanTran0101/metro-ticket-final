import uuid
import random
import string
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import text
from sqlalchemy.orm import Session

from booking_service.app.db import get_db
from booking_service.app.schemas import (
    BookingCreateRequest,
    BookingResponse,
    BookingUpdateRequest,
)

from booking_service.app.clients.scheduler_client import SchedulerClient

router = APIRouter()

@router.post("/booking/post/trip_confirm", response_model=BookingResponse)
def create_booking(
    req: BookingCreateRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db)
):
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user context")
    
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
                :total, 'Pending', :code, NOW()
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
        }

    row = db.execute(sql,params).mappings().first()
    db.commit()
    return BookingResponse(
        booking_id=booking_id,
        trip_id=req.trip_id,
        user_id=x_user_id,
        seats=req.seats_reserved,
        seat_fare=seat_fare,
        total_amount=total_amount,
        status="Pending",
        booking_code=booking_code,
        created_at=row["created_at"],
    )


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
        created_at=row["created_at"],
        paid_at=row["paid_at"],
        cancelled_at=row["cancelled_at"],
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