from typing import Optional, Dict, Any

from libs.http import HttpClient
from payment_service.app.settings import settings

class OtpClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self._client = HttpClient(base_url or settings.OTP_SERVICE_URL)

    def generate_otp(self, booking_id: str, user_id: str, amount: float, email: str, trip_id: str = None) -> Dict[str, Any]:
        payload = {
            "booking_id": booking_id,
            "user_id": user_id,
            "amount": amount,
            "email": email,
            "trip_id": trip_id,
            "status": "PENDING"
        }
        resp = self._client.post("/internal/post/otp/generate", json = payload)
        return resp.json()

    def verify_otp(self, booking_id: str, otp_code: str, user_id: str = None) -> Dict[str, Any]:
        payload = {
            "booking_id": booking_id,
            "otp_code": otp_code
        }
        headers = {}
        if user_id:
            headers["X-User-Id"] = user_id
        resp = self._client.post("/internal/post/otp/verify", json=payload, headers=headers)
        return resp.json()