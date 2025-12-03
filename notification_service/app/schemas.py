from pydantic import BaseModel
from typing import Optional

class SendReceiptRequest(BaseModel):
    user_id: str
    email: str
    amount: float
    journey_code: str
    date: str