import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import text
from sqlalchemy.orm import Session

from account_service.app.db import get_db
from account_service.app.schemas import (
    LoginRequest,
    LoginResponse,
    AccountResponse,
    DeductionRequest,
    BalanceOperationResponse,
)
from account_service.app.security import verify_password_hash

router = APIRouter()

#authentication
@router.post("/internal/post/account/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """
    internal endpoint for authentication
    """
    sql = text(
         """
        SELECT user_id::text AS user_id, password_hash, full_name, email, passenger_type
        FROM accounts
        WHERE username = :username
        """
    )
    row = db.execute(sql, {"username": req.username}).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not verify_password_hash(row["password_hash"], req.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    #return all the userid + claims
    return LoginResponse(
        userId=row["user_id"],
        claims={
            "name": row["full_name"],
            "email": row["email"],
            "role": row["passenger_type"] or "STANDARD" 
        },
    )
#query user information except password
@router.get("/internal/get/account/me", response_model=AccountResponse)
def get_me(x_user_id: str | None = Header(default=None, alias="X-User-Id"), db: Session = Depends(get_db)) -> AccountResponse:
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user context")
    
    sql = text(
        """
        SELECT user_id::text AS user_id, username, full_name, phone_number, 
               balance::float8 AS balance, email, passenger_type
        FROM accounts
        WHERE user_id = :uid
        """
    )
    row = db.execute(sql, {"uid": x_user_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return AccountResponse(
        user_id=row["user_id"],
        username=row["username"],
        full_name=row["full_name"],
        email=row["email"],
        balance=row["balance"],
        phone_number=row["phone_number"],
        passenger_type=row["passenger_type"] or "STANDARD" #standard for default
    )

#update the balance
@router.post("/internal/post/account/deduct", response_model=BalanceOperationResponse)
def deduct_balance(req: DeductionRequest, db: Session = Depends(get_db)):
    """
    the amount must not greater than balance
    """
    sql = text(
        """
        UPDATE accounts
        SET balance = balance - :amount
        WHERE user_id = :user_id AND balance >= :amount
        RETURNING balance
        """
    )
    result = db.execute(sql, {"amount": req.amount, "user_id": req.user_id}).mappings().first()
    db.commit()

    if not result:
        #if any failure for result = 1: user not exists, 2: insufficient balance
        user_check = db.execute(text("SELECT 1 FROM accounts WHERE user_id = :uid"), {"uid": req.user_id}).first()
        if not user_check:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        else:
            raise HTTPException(status_code=400, detail="Insufficient balance")

    return {
        "ok": True, 
        "new_balance": float(result["balance"]), 
        "message": "Transaction successful"
    }