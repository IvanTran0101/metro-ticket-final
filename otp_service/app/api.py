from fastapi import APIRouter, HTTPException, status, Header
import random
import time

from otp_service.app.cache import get_otp, del_otp, set_otp
from otp_service.app.settings import settings
from otp_service.app.schemas import (
    VerifyOTPRequest,
    VerifyOTPResponse,
    OTPVerifiedData,
    VerifyOTPErrorResponse,
    GenerateOTPRequest,
    GenerateOTPResponse, 
)


router = APIRouter()

def _generate_otp_code(length: int) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(max(4, length)))

@router.post("/internal/post/otp/generate", response_model=GenerateOTPResponse)
def generate_otp(body: GenerateOTPRequest) -> GenerateOTPResponse:
    otp_code = _generate_otp_code(settings.OTP_LENGTH)
    ttl_sec = settings.OTP_TTL_SEC
    expires_at = int(time.time()) + ttl_sec
    
    cache_data = {
        "otp_code": otp_code,
        "user_id": body.user_id,
        "amount": body.amount,
        "trip_id": body.trip_id,
        "booking_id": body.booking_id,
        "status": body.status,
    }

    try:
        set_otp(body.booking_id, cache_data, ttl_sec)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cache OTP")

    return GenerateOTPResponse(
        success=True,
        booking_id=body.booking_id,
        user_id=body.user_id,
        trip_id=body.trip_id,
        expires_at=expires_at,
    )

@router.post("/internal/post/otp/verify", response_model = VerifyOTPResponse, responses={ status.HTTP_400_BAD_REQUEST: {"model": VerifyOTPErrorResponse}})
def verify_otp(body: VerifyOTPRequest, x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> dict:
    # Gateway should have verified JWT and injected X-User-Id
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user context")

    rec = get_otp(body.booking_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP not found or expired")

    # Compare code; UI handles rate limiting, no attempt tracking here
    if str(rec.get("otp_code")) != str(body.otp_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    # Success: clear cache and notify
    del_otp(body.booking_id)
    return VerifyOTPResponse(message="OTP verified successfully. Transaction authorized.",
        data = OTPVerifiedData(
            user_id=rec["user_id"],
            amount=rec["amount"],
            trip_id=rec["trip_id"],
            booking_id=rec["booking_id"],
            status="Authorized"
        )
    )