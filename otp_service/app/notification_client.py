from typing import Optional, Dict, Any

from libs.http import HttpClient
from otp_service.app.settings import settings

class NotificationClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self._client = HttpClient(base_url or settings.NOTIFICATION_SERVICE_URL)

    def send_otp(self, booking_id: str, otp_code: str, user_id: str, email: str) -> Dict[str, Any]:
        payload = {
            "booking_id": booking_id,
            "otp_code": otp_code,
            "user_id": user_id,
            "email": email,
        }
        resp = self._client.post("/internal/notification/send_otp", json = payload)
        return resp.json()