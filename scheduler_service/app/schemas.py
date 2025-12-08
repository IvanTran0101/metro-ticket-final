from pydantic import BaseModel, Field
from datetime import date, time
from typing import List, Optional

class MetroLine(BaseModel):
    line_id: str
    name: str
    code: str | None = None
    color: str | None = None

    class Config: 
        orm_mode = True

class Station(BaseModel):
    station_id: str
    name: str
    address: str | None = None
    lat: float | None = None
    long: float | None = None

    class Config:
        orm_mode = True


class RouteSearchRequest(BaseModel):
    from_station: str = Field(..., description="Mã ga đi ")
    to_station: str = Field(..., description="Mã ga đến ")

class FareResponse(BaseModel):
    from_station_name: str
    to_station_name: str
    distance_km: float
    
    standard_fare: float 
    
    estimated_time_mins: int
    route_description: str | None = None

class InternalFareRequest(BaseModel):
    from_station: str
    to_station: str
    passenger_type: str = "STANDARD" 

class InternalFareResponse(BaseModel):
    base_fare: float      
    distance_fare: float 
    total_amount: float   
    currency: str = "VND"


class NextTrainInfo(BaseModel):
    line_name: str        
    direction: str       
    departure_time: time  
    minutes_left: int     
    train_code: str | None = None 

class StationScheduleResponse(BaseModel):
    station_id: str
    station_name: str
    current_time: str
    next_trains: List[NextTrainInfo]



class StationCreate(BaseModel):
    station_id: str
    name: str
    distance_from_start: float

