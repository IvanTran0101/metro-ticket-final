from email.policy import default
import uuid
import json
import redis 
from payment_service.app.settings import settings
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Header, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List

from payment_service.app.db import get_db
from payment_service.app.schemas import (
    PaymentInitRequest,
    PaymentInitResponse,
    PaymentStatus,
    PaymentVerifyRequest,
    PaymentVerifyResponse,
    PaymentHistoryResponse,
)

from payment_service.app.client.account_client import AccountClient
from payment_service.app.client.booking_client import BookingClient
from payment_service.app.client.scheduler_client import SchedulerClient
from payment_service.app.client.notification_client import NotificationClient
from payment_service.app.client.otp_client import OtpClient

router = APIRouter()
r = redis.Redis.from_url(settings.REDIS_URL, decode_responses= True)
@router.post("/post/payment/payment_init", response_model=PaymentInitResponse)
def init_payment(
    req: PaymentInitRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
    db: Session = Depends(get_db)
):
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Missing user context")

    if idempotency_key:
        cache_key = f"idempotency:{idempotency_key}"
        cache_data = r.get(cache_key)
        if cache_data:
            print(f"Idempotency hit: {idempotency_key}")
            return PaymentInitResponse(**json.loads(cache_data))
    
    account_client = AccountClient()
    if not account_client.verify_pin(x_user_id, req.pin):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail= "Invalid PIN") 

    otp_client = OtpClient()
    email = x_user_email or "user@example.com"
    try:
        otp_client.generate_otp(req.booking_id, x_user_id, req.amount, email, req.trip_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail = "Failed to generate OTP")

    response = PaymentInitResponse(booking_id=req.booking_id, message="OTP sent to email")

    if idempotency_key:
        cache_key = f"idempotency: {idempotency_key}"
        r.setex(cache_key, 86400, response.json())
    return response

@router.post("/post/payment/verify_otp", response_model=PaymentVerifyResponse)
def verify_otp(
    req: PaymentVerifyRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
    db: Session = Depends(get_db)
):
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user context")
    
    booking_id = req.booking_id

    otp_client = OtpClient()
    try:
        verify_resp = otp_client.verify_otp(booking_id, req.otp_code, x_user_id)
        if not verify_resp.get("success"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="verification failed")

    otp_data = verify_resp.get("data", {})
    amount = float(otp_data.get("amount",0))
    trip_id = otp_data.get("trip_id")

    payment_id = str(uuid.uuid4())
    sql = text(
        """
        INSERT INTO payments (payment_id, booking_id, user_id, amount, status, expires_at)
        VALUES (:pid, :bid, :uid, :amt, :status, NOW() + INTERVAL '15 minutes')
        """
    )
    db.execute(sql, {
        "pid": payment_id,
        "bid": booking_id,
        "uid": x_user_id,
        "amt": amount,
        "status": PaymentStatus.PENDING.value
    })
    db.commit()

    booking_client = BookingClient()
    scheduler_client = SchedulerClient()
    
    try: 
        booking_client.booking_update(booking_id, trip_id)
    
        if trip_id:
            scheduler_client.seat_update(trip_id, booking_id)
    except Exception:
        db.execute(text("UPDATE payments SET status = 'FAILED' WHERE payment_id = :pid"), {"pid": payment_id})
        db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to confirm booking")

    account_client = AccountClient()
    try:
        account_client.balance_update(x_user_id,amount)
    except Exception:
        db.execute(text("UPDATE payments SET status = 'FAILED' WHERE payment_id = :pid"), {"pid": payment_id})
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")

    db.execute(text("UPDATE payments SET status = :status, complete_at = NOW() WHERE payment_id = :pid"),
    {"status": PaymentStatus.COMPLETED.value, "pid": payment_id})
    db.commit()

    notification_client = NotificationClient()
    try:
        email = x_user_email or "user@example.com"
        notification_client.send_receipt(payment_id, booking_id, x_user_id, email, amount)
    except Exception:
        pass

    return PaymentVerifyResponse(ok = True, message="Payment successful")

@router.get("/get/payment/history", response_model=List[PaymentHistoryResponse])
def get_payment_history(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    #Return the 10 most recent payments
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user context")
    
    sql = text(
                """
                SELECT payment_id, booking_id, user_id, amount, complete_at, expires_at, status
                FROM payments
                WHERE user_id = :uid
                ORDER BY complete_at DESC
                LIMIT 10
                """
            )
    rows = db.execute(sql, {"uid": x_user_id}).mappings().all()

    result = []
    for r in rows:
        rec = {
            "payment_id": str(r["payment_id"]),
            "booking_id": str(r["booking_id"]),
            "user_id": str(r["user_id"]),
            "amount": float(r["amount"]),
            "complete_at": r["complete_at"],
            "expires_at": r["expires_at"],  
            "status": r["status"],
        }
        result.append(rec)

    return result

@router.post("/internal/post/payment/otp_expires")
def otp_expires(booking_id: str):
    booking_client = BookingClient()
    scheduler_client = SchedulerClient()
    
    try:
        # Unlock booking and get trip_id
        booking_resp = booking_client.booking_unlock(booking_id)
        trip_id = booking_resp.get("trip_id")
        
        if trip_id:
            # Release seat lock
            scheduler_client.seat_canceled(trip_id, booking_id)
            
    except Exception:
        # Log error but don't fail the request as this is cleanup
        pass
        
    return {"ok": True}