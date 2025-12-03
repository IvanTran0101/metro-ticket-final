from typing import Dict, Any, Optional
from libs.http import HttpClient
from journey_service.app.settings import settings


class SchedulerClient:
    def __init__(self):
        self._client = HttpClient(settings.SCHEDULER_SERVICE_URL)

    def calculate_fare(self, from_station: str, to_station: str, passenger_type: str = "STANDARD")-> Dict[str, Any]:

        payload = {
            "from_station": from_station,
            "to_station": to_station,
            "passenger_type": passenger_type
        }
        resp = self._client.post("/internal/calculate-fare", json= payload)
        return resp.json()