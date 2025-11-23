from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user_id: str
    access_token: str
    token_type: str = "bearer"
    expire_time: int
