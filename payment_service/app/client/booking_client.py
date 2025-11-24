from typing import Optional, Dict, Any

from libs.http import HttpClient
from payment_service.app.settings import settings

class BookingClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self._client = HttpClient(base_url or settings.BOOKING_SERVICE_URL)

    def booking_update(self, booking_id: str,trip_id: str) -> Dict[str, Any]:
        payload = {
            "booking_id": booking_id,
            "trip_id": trip_id
        }
        resp = self._client.post("/internal/post/booking/booking_update", json = payload)
        return resp.json()