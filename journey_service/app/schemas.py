from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


#mue ve
class PurchaseRequest(BaseModel):
    from_station: str = Field(..., description="Departure Station")
    to_station: str = Field(...,description= "Arrival Station")
    ticket_type: str = "SINGLE" # SINGLE, RETURN, DAY, MONTH

class PurchaseResponse(BaseModel):
    journey_code: str
    fare_amount: float
    message:str

#gate simulator

class GateRequest(BaseModel):
    journey_code: str = Field(...,description= "6 Digits code")
    station_id: str = Field(..., description= "Current Station")

class GateResponse(BaseModel):
    ok: bool
    message: str
    gate_action: str = "OPEN" #OPEN, STOP

class PenaltyPaymentRequest(BaseModel):
    journey_code: str
    amount: float

#history
class JourneyHistoryItem(BaseModel):
    journey_id: UUID
    journey_code: str
    check_in_station_id: str
    check_out_station_id: Optional[str]
    fare_amount: float
    status: str
    created_at: datetime

    class Config:
        orm_mode = True

class TicketItem(BaseModel):
    ticket_id: UUID
    ticket_code: str
    ticket_type: str
    origin_station_id: Optional[str]
    destination_station_id: Optional[str]
    status: str
    remaining_trips: Optional[int]
    valid_until: Optional[datetime]
    created_at: datetime
    
    class Config:
        orm_mode = True