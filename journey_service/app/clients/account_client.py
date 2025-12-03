from typing import Dict, Any
from libs.http import HttpClient
from journey_service.app.settings import settings

class AccountClient:
    def __init__(self):
        self._client = HttpClient(settings.ACCOUNT_SERVICE_URL)

    def get_me(self, user_id: str) -> Dict[str, Any]:
        resp = self._client.get("/internal/get/account/me", headers= {"X-User-Id": user_id})
        return resp.json()

    def deduct_balance(self, user_id: str, amount:float, desc: str = "Payment") -> Dict[str, Any]:
        payload = {
            "user_id": user_id,
            "amount": amount,
            "description": desc
        }
        resp = self._client.post("/internal/post/account/deduct", json=payload)
        return resp.json()

    def top_up(self, user_id: str, amount: float):
        payload = {"user_id": user_id, "amount": amount}
        self._client.post("/internal/post/account/topup", json=payload)