from enum import Enum
from pydantic import BaseModel, Field

class PaymentStatus(str,Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    
class PaymentInitRequest(BaseModel):
    booking_id: str
    amount: int

class PaymentInitResponse(BaseModel):
    payment_id: str
    message: str

class PaymentVerifyRequest(BaseModel):
    payment_id: str
    otp_code: str
    
class PaymentVerifyResponse(BaseModel):
    ok: bool
    message: str
