from typing import Optional, Dict, Any

from libs.http import HttpClient
from payment_service.app.settings import settings

class NotificationClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self._client = HttpClient(base_url or settings.NOTIFICATION_SERVICE_URL)

    def send_receipt(self, payment_id: str, booking_id: str, user_id: str, email: str, amount: float) -> Dict[str, Any]:
        payload = {
            "payment_id": payment_id,
            "booking_id": booking_id,
            "user_id": user_id,
            "email": email,
            "amount": amount,
        }
        resp = self._client.post("/internal/post/notification/send_receipt", json = payload)
        return resp.json()