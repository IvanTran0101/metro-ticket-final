from dataclasses import Field
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


#mue ve
class PurchaseRequest(BaseModel):
    from_station: str = Field(..., description="Departure Station")
    to_station: str = Field(...,description= "Arrival Station")

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
    gate_action str = "OPEN" #OPEN, STOP

class PenaltyPaymentRequest(BaseModel):
    journey_code: str
    amount: float
    auto_topup: bool = False # Thêm cờ này

#history
class JourneyHistoryItem(BaseModel):
    journey_id: str
    journey_code: str
    check_in_station: str
    check_out_station: Optional[str]
    fare_amount: float
    status: str
    create_at: datetime