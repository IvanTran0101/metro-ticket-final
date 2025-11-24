from typing import Dict, Any, Optional
from libs.http import HttpClient
from booking_service.app.settings import settings


class SchedulerClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self._client = HttpClient(base_url or settings.SCHEDULER_SERVICE_URL)

    def lock_seat(self, trip_id: str, booking_id: str, seats: int) -> Dict[str, Any]:
        """
        Calls scheduler service to lock seats.
        Endpoint: POST /internal/post/route/seat/lock
        """
        payload = {
            "trip_id": trip_id,
            "booking_id": booking_id,
            "seats_reserved": seats
        }
        resp = self._client.post("/internal/post/route/seat/lock", json=payload)
        return resp.json()

    def get_trip(self, trip_id: str) -> Dict[str, Any]:
        resp = self._client.get(f"/internal/get/route/trip/{trip_id}")
        return resp.json()