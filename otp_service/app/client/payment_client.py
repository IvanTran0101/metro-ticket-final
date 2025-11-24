from typing import Optional, Dict, Any

from libs.http import HttpClient
from otp_service.app.settings import settings


class PaymentClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self._client = HttpClient(base_url or settings.PAYMENT_SERVICE_URL)

    def otp_expires(self, booking_id: str) -> Dict[str, Any]:
        resp = self._client.post(f"/internal/post/payment/otp_expires?booking_id={booking_id}")
        return resp.json()
