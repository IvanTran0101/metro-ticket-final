from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
import datetime

class TransactionCreate(BaseModel):
    user_id: str
    amount: float
    type: str = "TICKET_PAYMENT" #TICKET_PAYMENT, TOP_UP, PENALTY
    journey_id: Optional[str] = None
    description: Optional[str] = None

class TransactionResponse(BaseModel):
    transaction_id: str
    user_id: str
    amount:float
    type: str
    description: Optional[str]
    created_at: datetime

    journey_id: Optional[str]
    