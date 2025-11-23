from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password_hash: str


class LoginResponse(BaseModel):
    userId: str
    claims: dict[str, str]


class AccountResponse(BaseModel):
    userId: str
    name: str
    email: str
    balance: float
    phone_number: str


class BalanceUpdateRequest(BaseModel):
    user_id: str
    amount: float

