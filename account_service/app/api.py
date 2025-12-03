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
    PinVerifyRequest,
    BalanceUpdateRequest,
)
from account_service.app.security import verify_password_hash

router = APIRouter()

# --- 1. AUTHENTICATION & PROFILE ---

@router.post("/internal/post/account/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    # Authentication Service sẽ gọi API này để verify user
    # Cần lấy thêm passenger_type để Auth Service có thể (tùy chọn) lưu vào Token
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

    return LoginResponse(
        userId=row["user_id"],
        claims={
            "name": row["full_name"],
            "email": row["email"],
            "role": row["passenger_type"] or "STANDARD" # Thêm thông tin này
        },
    )

@router.get("/internal/get/account/me", response_model=AccountResponse)
def get_me(x_user_id: str | None = Header(default=None, alias="X-User-Id"), db: Session = Depends(get_db)) -> AccountResponse:
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user context")
    
    # Update: Lấy thêm passenger_type
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
        passenger_type=row["passenger_type"] or "STANDARD" # Mặc định là STANDARD
    )

# --- 2. PAYMENT & WALLET LOGIC ---

@router.post("/internal/post/account/deduct", response_model=BalanceOperationResponse)
def deduct_balance(req: DeductionRequest, db: Session = Depends(get_db)):
    """
    API mới thay thế cho balance_update cũ.
    Thực hiện trừ tiền an toàn (Atomic Update) có kiểm tra số dư.
    """
    # Câu lệnh SQL này đảm bảo: Chỉ trừ tiền nếu số dư >= số tiền trừ
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
        # Nếu không có dòng nào được update, nghĩa là user không tồn tại HOẶC thiếu tiền
        # Check kỹ hơn để trả về lỗi đúng
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

@router.post("/internal/post/account/verify_pin")
def verify_pin(req: PinVerifyRequest, db: Session = Depends(get_db)):
    """Giữ nguyên API này để xác thực lúc Mua vé (Purchase)"""
    sql = text("SELECT pin_hash FROM accounts WHERE user_id = :uid")
    row = db.execute(sql, {"uid": req.user_id}).mappings().first()

    if not row: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Lưu ý: Cần đảm bảo logic hash PIN khớp với lúc seed/tạo user
    hashed_input_pin = hashlib.sha256(req.pin.encode()).hexdigest()

    if row["pin_hash"] != hashed_input_pin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PIN")
        
    return {"valid": True}

# account_service/app/api.py

@router.post("/internal/post/account/topup")
def top_up(req: BalanceUpdateRequest, db: Session = Depends(get_db)):
    """API nạp tiền khẩn cấp (dùng khi thiếu tiền đóng phạt)"""
    sql = text("""
        UPDATE accounts 
        SET balance = balance + :amount 
        WHERE user_id = :uid 
        RETURNING balance
    """)
    res = db.execute(sql, {"amount": req.amount, "uid": req.user_id}).mappings().first()
    db.commit()
    return {"ok": True, "new_balance": float(res["balance"])}