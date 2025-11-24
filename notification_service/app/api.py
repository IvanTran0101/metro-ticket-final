from fastapi import APIRouter, HTTPException, status, Header
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

import os
from notification_service.app.settings import settings
from libs.http.client import HttpClient
from notification_service.app.schemas import (
    SendOTPRequest,
    SendReceiptRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/internal/notify/send_otp", status_code = status.HTTP_202_ACCEPTED)
def send_otp(req: SendOTPRequest) -> dict:
    try:
        _send_otp_email_request(
            email=req.email,
            booking_id=req.booking_id,
            otp_code=req.otp_code
        )
        return {"ok": True, "message": "OTP email processing initiated."}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to send OTP email."
        )
    
@router.post("/internal/notify/send_receipt", status_code=status.HTTP_202_ACCEPTED)
def send_receipt(req: SendReceiptRequest) -> dict:
    try:
        _send_receipt_email_request(
            email=req.email,
            payment_id=req.payment_id,
            amount=req.amount
        )
        return {"ok": True, "message": "Receipt email processing initiated."}
    except Exception:
        raise HTTPException (
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to send receipt email."
        )

def _send_email(to: str, subject: str, body: str) -> None:
    """Send HTML email via SMTP"""
    if settings.DRY_RUN:
        logger.info("[DRY RUN] email to=%s subject=%s", to, subject)
        return
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to
        msg.attach(MIMEText(body, "html", "utf-8"))
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to, msg.as_string())
        
        logger.info("Email sent to %s subject=%s", to, subject)
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise

def _send_otp_email_request(email: str, booking_id: str, user_id: str, otp_code: str) -> None:
    
    if not email or "@" not in email:
        logger.warning("OTP email skipped: Invalid email for user_id=%s", user_id)
        return

    subject = "Your OTP Code"
    body = f"""
        <h2>Your OTP Code</h2>
        <p>Your OTP code is: <strong style="font-size: 24px;">{otp_code}</strong></p>
        <p>Booking ID: {booking_id}</p>
        <p>This code expires in 5 minutes.</p>
        """
    
    _send_email(to=email, subject=subject, body=body)
    logger.info("OTP Email dispatched payment_id=%s to=%s", booking_id, email)

def _send_receipt_email_request(email: str, payment_id: str, amount: float) -> None:
    if amount is None:
        logger.warning("Receipt email skipped: Missing amount for payment_id=%s", payment_id)
        return
        
    subject = "Payment Receipt"
    body = f"""
        <h2>✅ Payment Successful</h2>
        <p>Payment ID: {payment_id}</p>
        <p>Amount: ${amount:,.2f}</p>
        <p>Thank you for your payment!</p>
        """
    
    _send_email(to=email, subject=subject, body=body)
    logger.info("Receipt Email dispatched payment_id=%s to=%s", payment_id, email)