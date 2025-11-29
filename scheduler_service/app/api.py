import json
from datetime import datetime, timedelta

import redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from scheduler_service.app.db import get_db
from scheduler_service.app.schemas import (
    TripResponse,
    SeatLockRequest,
    SeatLockResponse,
    SeatLockResponse,
    SeatUpdateRequest,
    TripSearchRequest,
)
from scheduler_service.app.settings import settings

router = APIRouter()

r = redis.Redis.from_url(settings.REDIS_URL, decode_responses= True)

@router.post("/post/route/trips", response_model=list[TripResponse])
def search_trip(
    req: TripSearchRequest,
    db: Session = Depends(get_db)
):
    # Get current date and time
    now = datetime.now()
    current_date = now.date()
    current_time = now.time()

    # Base query: Only show Scheduled trips
    query = "SELECT * FROM trips WHERE status = 'Scheduled'"
    params = {}

    # Filter out trips that have already departed
    # Logic: (date_departure > current_date) OR (date_departure = current_date AND departure_time > current_time)
    query += " AND (date_departure > :current_date OR (date_departure = :current_date AND departure_time > :current_time))"
    params["current_date"] = current_date
    params["current_time"] = current_time

    if req.from_station:
        query += " AND from_station_name = :from_station"
        params["from_station"] = req.from_station
    if req.to_station:
        query += " AND to_station_name = :to_station"
        params["to_station"] = req.to_station
    
    if req.date:
        query += " AND date_departure = :date"
        params["date"] = req.date
    
    trips = db.execute(text(query), params).mappings().all()

    results = []
    for trip in trips:
        trip_dict = dict(trip)
        
        # Convert UUID to string for JSON serialization
        trip_dict["trip_id"] = str(trip_dict["trip_id"])

        locked_keys = r.keys(f"lock:{trip_dict['trip_id']}:*")
        total_locked = 0

        for key in locked_keys:
            data = r.get(key)
            if data:
                try:
                    lock_data = json.loads(data)
                    total_locked += lock_data.get("seats",0)
                except Exception:
                    pass
        
        trip_dict["remaining_seats"] -= total_locked

        results.append(trip_dict)

    return results

@router.post("/internal/post/route/seat/lock", response_model=SeatLockResponse)
def lock_seat(req: SeatLockRequest, db: Session = Depends(get_db)):
    
    trip_sql = text("SELECT remaining_seats FROM trips WHERE trip_id = :trip_id")
    trip = db.execute(trip_sql,{"trip_id":
    req.trip_id}).mappings().first()

    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    locked_keys = r.keys(f"lock:{req.trip_id}:*")
    total_locked_in_redis = 0
    for key in locked_keys:
        data = r.get(key)
        if data:
            try: 
                lock_data = json.loads(data)
                total_locked_in_redis += lock_data.get("seats",0)
            except Exception:
                pass
    
    real_remaining = trip["remaining_seats"] - total_locked_in_redis
    if real_remaining < req.seats_reserved:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not enough seats")

    lock_key = f"lock:{req.trip_id}:{req.booking_id}"

    expires_at = datetime.now() + timedelta(minutes=10)

    lock_data = {
        "trip_id": req.trip_id,
        "booking_id": req.booking_id,
        "seats": req.seats_reserved,
        "status": "Locked",
        "expires_at": expires_at.isoformat()
    }

    r.setex(lock_key, 600, json.dumps(lock_data))

    return SeatLockResponse(
        trip_id = req.trip_id,
        seats_reserved = req.seats_reserved,
        expires_at=expires_at.isoformat(),
        status="Locked"

    )

@router.post("/internal/post/route/seat_update")
def update_seat(req: SeatUpdateRequest,db: Session = Depends(get_db)):
    lock_key = f"lock:{req.trip_id}:{req.booking_id}"
    data = r.get(lock_key)

    if not data:
        return {"ok": False, "message": "Lock not found or expire"}

    lock_data = json.loads(data)
    seat_to_deduct = lock_data.get("seats", 0)

    update_sql = text(
        "UPDATE trips SET remaining_seats = remaining_seats - :seats WHERE trip_id= :trip_id"

    )
    db.execute(update_sql,{"seats": seat_to_deduct, "trip_id":req.trip_id})
    db.commit()

    r.delete(lock_key)

    return {"ok": True, "message": "Seats confirmed and lock released"}

@router.get("/internal/get/route/trip/{trip_id}", response_model=TripResponse)
def get_trip_details(trip_id: str, db: Session = Depends(get_db)):
    sql = text("SELECT * FROM trips WHERE trip_id = :trip_id")
    row = db.execute(sql,{"trip_id": trip_id}).mappings().first()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    trip_dict = dict(row)
    
    # Convert UUID to string for JSON serialization
    trip_dict["trip_id"] = str(trip_dict["trip_id"])
    
    locked_keys = r.keys(f"lock:{trip_id}:*")
    total_locked = 0
    for key in locked_keys:
        data = r.get(key)
        if data:
            try:
                lock_data = json.loads(data)
                total_locked += lock_data.get("seats",0)
            except Exception:
                pass
    
    trip_dict["remaining_seats"] -= total_locked
    return trip_dict

@router.post("/internal/post/route/seat_canceled")
def cancel_seat(trip_id: str, booking_id: str):
    lock_key = f"lock:{trip_id}:{booking_id}"
    r.delete(lock_key)
    return {"ok": True}
