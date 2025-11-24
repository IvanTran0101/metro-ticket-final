from pydantic import BaseModel
from typing import Optional


class VerifyOTPRequest(BaseModel):
    otp_code: str
    booking_id: str


class OTPVerifiedData(BaseModel):
    user_id: str
    amount : float
    trip_id: str | None = None
    booking_id: str | None = None
    status: str 


class VerifyOTPResponse(BaseModel):
    success: bool = True
    message: str | None = None
    data: OTPVerifiedData | None = None


class OTPErrorDetail(BaseModel):
    code: str
    message: str


class VerifyOTPErrorResponse(BaseModel):
    success: bool = False
    error: OTPErrorDetail

class GenerateOTPRequest(BaseModel):
    user_id: str | None = None
    booking_id: str | None = None
    trip_id: str | None = None
    amount: float
    status: str 


class GenerateOTPResponse(BaseModel):
    success: bool
    booking_id: str | None = None
    trip_id: str | None = None
    user_id: str
    expires_at: int