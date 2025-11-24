from typing import Optional, Dict, Any

from libs.http import HttpClient
from payment_service.app.settings import settings

class SchedulerClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self._client = HttpClient(base_url or settings.SCHEDULER_SERVICE_URL)

    def seat_update(self,trip_id: str, booking_id: str) -> Dict[str, Any]:
        payload = {
            "booking_id": booking_id,
            "trip_id": trip_id,
        }
        resp = self._client.post("/internal/post/route/seat_update", json = payload)
        return resp.json()