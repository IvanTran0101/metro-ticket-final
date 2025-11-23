from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import text
from sqlalchemy.orm import Session

from account_service.app.db import get_db
from account_service.app.schemas import (
    LoginRequest,
    LoginResponse,
    AccountResponse,
    BalanceUpdateRequest,
)
from account_service.app.security import verify_password_hash

router = APIRouter()

@router.post("/internal/post/account/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    sql = text(
         """
        SELECT user_id::text AS user_id, password_hash, full_name, email
        FROM accounts
        WHERE username = :username
        """
    )
    row = db.execute(sql, {"username": req.username}).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not verify_password_hash(row["password_hash"], req.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return LoginResponse(
        userId=row["user_id"],
        claims={
            "name": row["full_name"],
            "email": row["email"],
        },
    )

@router.get("/internal/get/account/me", response_model=AccountResponse)
def get_me(x_user_id: str | None = Header(default=None, alias="X-User-Id"), db: Session = Depends(get_db)) -> AccountResponse:

    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user context")
    
    sql = text(
        """
        SELECT user_id::text AS user_id, full_name, phone_number, balance::float8 AS balance, email
        FROM accounts
        WHERE user_id = :uid
        """
    )
    row = db.execute(sql, {"uid": x_user_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return AccountResponse(
        userId=row["user_id"],
        name=row["full_name"],
        email=row["email"],
        balance=row["balance"],
        phone_number=row["phone_number"],
    )

@router.post("/internal/post/account/balance_update")
def balance_update(req: BalanceUpdateRequest, db: Session = Depends(get_db)):
    # User requested to subtract the amount (payment context)
    sql = text(
        """
        UPDATE accounts
        SET balance = balance - :amount
        WHERE user_id = :user_id
        RETURNING balance
        """
    )
    result = db.execute(sql, {"amount": req.amount, "user_id": req.user_id})
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {"ok": True}