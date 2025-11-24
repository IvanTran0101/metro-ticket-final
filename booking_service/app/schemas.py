from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BookingCreateRequest(BaseModel):
    trip_id: str
    seats_reserved: int


class BookingResponse(BaseModel):
    booking_id: str
    trip_id: str
    user_id: str
    seats: int
    seat_fare: float
    total_amount: float
    status: str
    booking_code: str
    created_at: datetime
    paid_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None


class BookingUpdateRequest(BaseModel):
    status: str
