from pydantic import BaseModel
from datetime import date, time


class TripResponse(BaseModel):
    trip_id: str
    brand: str
    from_station_name: str
    to_station_name: str
    date_departure: date
    departure_time: time
    capacity: int
    remaining_seats: int
    status: str
    route_name: str
    fare_per_seat: float


class SeatLockRequest(BaseModel):
    trip_id: str
    seats_reserved: int


class SeatLockResponse(BaseModel):
    trip_id: str
    seats_reserved: int
    expires_at: str
    status: str


class SeatUpdateRequest(BaseModel):
    trip_id: str
    booking_id: str
