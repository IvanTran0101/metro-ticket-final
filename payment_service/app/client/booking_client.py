from typing import Optional, Dict, Any

from libs.http import HttpClient
from payment_service.app.settings import settings

class BookingClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self._client = HttpClient(base_url or settings.BOOKING_SERVICE_URL)

    def booking_update(self, booking_id: str, trip_id: str) -> Dict[str, Any]:
        # trip_id is unused in this update, but kept for signature compatibility
        payload = {
            "booking_id": booking_id,
            "status": "Paid"
        }
        resp = self._client.post(f"/internal/post/booking/booking_update?booking_id={booking_id}", json=payload)
        return resp.json()

    def booking_unlock(self, booking_id: str) -> Dict[str, Any]:
        resp = self._client.post(f"/internal/post/booking/booking_unlock?booking_id={booking_id}")
        return resp.json()