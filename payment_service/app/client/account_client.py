from typing import Optional, Dict, Any

from libs.http import HttpClient
from payment_service.app.settings import settings

class AccountClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self._client = HttpClient(base_url or settings.ACCOUNT_SERVICE_URL)

    def get_me(self,user_id: str) -> Dict[str, Any]:
        headers = {"X-User-Id": user_id}
        resp = self._client.get("/internal/get/account/me", headers=headers)
        return resp.json()
    
    def verify_pin(self, user_id: str, pin: str) ->bool:
        payload = {
            "user_id": user_id,
            "pin": pin
        }
        try:
            self._client.post("/internal/post/account/verify_pin", json=payload)
            return True
        except Exception:
            return False

    def balance_update(self, user_id: str, amount: float) -> Dict[str, Any]:

        payload = {
            "user_id": user_id,
            "amount": amount
        }

        resp = self._client.post("/internal/post/account/balance_update", json = payload)

        return resp.json()