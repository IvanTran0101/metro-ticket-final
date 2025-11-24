from pydantic import BaseModel
from typing import Optional

class SendOTPRequest(BaseModel):
    email: str
    booking_id: str
    otp_code: str
    
class SendReceiptRequest(BaseModel):
    email: str
    payment_id: str
    amount: float