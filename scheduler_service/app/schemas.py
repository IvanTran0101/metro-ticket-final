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

# --- 2. SEARCH & FARE CALCULATION (Quan trọng nhất cho Mua vé) ---

class RouteSearchRequest(BaseModel):
    from_station: str = Field(..., description="Mã ga đi ")
    to_station: str = Field(..., description="Mã ga đến ")

class FareResponse(BaseModel):
    from_station_name: str
    to_station_name: str
    distance_km: float
    
    # Giá vé chuẩn (chưa giảm giá)
    standard_fare: float 
    
    # Thông tin lộ trình gợi ý (Optional)
    estimated_time_mins: int
    route_description: str | None = None

# Schema dùng cho API nội bộ (Internal Call từ Journey Service)
class InternalFareRequest(BaseModel):
    from_station: str
    to_station: str
    passenger_type: str = "STANDARD" # Để tính giảm giá nếu Scheduler nắm logic này

class InternalFareResponse(BaseModel):
    base_fare: float      # Giá gốc từ bảng fare_rules
    distance_fare: float  # Giá tính theo km
    total_amount: float   # Tổng tiền cuối cùng
    currency: str = "VND"

# --- 3. REAL-TIME SCHEDULE (Cho màn hình thông tin) ---

class NextTrainInfo(BaseModel):
    line_name: str        # VD: Metro 1
    direction: str        # VD: Hướng Suối Tiên
    departure_time: time  # VD: 08:15:00
    minutes_left: int     # VD: 5 (còn 5 phút nữa tàu đến)
    train_code: str | None = None # VD: Hitachi-01

class StationScheduleResponse(BaseModel):
    station_id: str
    station_name: str
    current_time: str
    next_trains: List[NextTrainInfo]

# --- 4. DATA SEEDING / MANAGEMENT (Nếu cần API tạo dữ liệu) ---
# (Thường dùng script SQL rồi nên có thể bỏ qua hoặc làm đơn giản)

class StationCreate(BaseModel):
    station_id: str
    name: str
    distance_from_start: float

