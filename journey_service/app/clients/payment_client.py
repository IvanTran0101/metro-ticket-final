from libs.http import HttpClient
from journey_service.app.settings import settings

class PaymentClient:
    def __init__(self):
        self.client = HttpClient(settings.PAYMENT_SERVICE_URL)

    def log_transaction(self, user_id: str, amount: float, description: str, ticket_id: str = None, transaction_type: str = "TICKET_PAYMENT"):

        try:
            payload = {
                "user_id": str(user_id),
                "amount": amount,
                "type": transaction_type,
                "ticket_id": ticket_id,
                "description": description
            }
            self.client.post("/internal/log", json=payload)

        except Exception as e:
            print(f"Failed to log transaction: {e}")