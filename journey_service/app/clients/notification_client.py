from datetime import datetime
from libs.http import HttpClient
from journey_service.app.settings import settings
from journey_service.app.clients.account_client import AccountClient

class NotificationClient:
    def __init__(self):
        self.client = HttpClient(settings.NOTIFICATION_SERVICE_URL)
        self.account_client = AccountClient()

    def send_receipt(self, user_id: str, amount: float, journey_code: str = "UNKNOWN"):
        try:
            user_info = self.account_client.get_me(user_id)
            user_email = user_info.get("email")

            if not user_email:
                print(f"Skipping email reciept: No email found for user {user_id}")
                return 

            payload= {
                "user_id": user_id,
                "email": user_email,
                "amount": amount,
                "journey_code": journey_code,
                "date": datetime.now().strftime("%d/%m.%Y %H:%M")
            }

            self.client.post("/internal/post/notification/send_receipt", json=payload)

        except Exception as e:
            print(f"Failed to send receipt: {e}")