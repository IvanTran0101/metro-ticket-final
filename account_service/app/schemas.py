from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# --- 1. LOGIN & AUTH ---
class LoginRequest(BaseModel):
    username: str
    password_hash: str

class LoginResponse(BaseModel):
    userId: str
    claims: dict

# --- 2. ACCOUNT INFO ---
class AccountResponse(BaseModel):
    user_id: str
    username: str
    full_name: str
    email: str
    phone_number: str | None = None
    balance: float
    passenger_type: str  # 'STANDARD', 'STUDENT', 'ELDERLY'

# --- 3. INTERNAL ACTIONS (Dành cho Journey/Payment Service gọi) ---

class DeductionRequest(BaseModel):
    user_id: str
    amount: float = Field(..., gt=0, description="Số tiền cần trừ")
    description: str | None = "Thanh toán vé tàu"

class TopUpRequest(BaseModel):
    user_id: str
    amount: float = Field(..., gt=0, description="Số tiền nạp")

class BalanceOperationResponse(BaseModel):
    ok: bool
    new_balance: float
    message: str

# FIX: Bổ sung 2 class thiếu
class PinVerifyRequest(BaseModel):
    user_id: str
    pin: str

class BalanceUpdateRequest(BaseModel):
    user_id: str
    amount: float