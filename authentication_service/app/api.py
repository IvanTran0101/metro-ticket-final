from fastapi import APIRouter, HTTPException, status

from authentication_service.app.schemas import LoginRequest, LoginResponse
from authentication_service.app.security.jwt import create_access_token, hash_password
from authentication_service.app.settings import settings
from authentication_service.app.clients.account_client import AccountClient


router = APIRouter()


@router.post("/authentication/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    # Hash password before sending to account service
    pwd_hash = hash_password(body.password, settings.PASSWORD_SALT)

    try:
        user_data = client.verify_credentials(body.username, pwd_hash)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user_id = user_data.get("userId")
    claims = user_data.get("claims", {})
    token = create_access_token(subject=str(user_id or body.username), claims=claims)
    
    # Calculate expire time (same logic as in create_access_token)
    # We should ideally return the exact exp from token, but for now we use settings
    import time
    expire_time = int(time.time()) + settings.JWT_EXPIRES_MIN * 60

    return LoginResponse(
        user_id=str(user_id),
        access_token=token,
        expire_time=expire_time
    )
