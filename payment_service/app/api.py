from ast import alias
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header

from sqlalchemy import text
from sqlalchemy.orm import Session

from payment_service.app.db import get_db
from payment_service.app.schemas import (
    TransactionCreate, TransactionResponse
)

router = APIRouter()


@router.post("/internal/log", response_model=TransactionResponse)
def log_transaction(req: TransactionCreate, db: Session = Depends(get_db)):
    new_id = str(uuid.uuid4())
    sql = text("""
        INSERT INTO transactions (
            transaction_id, user_id, ticket_id, amount, type, description, 
            created_at) VALUES (
            :id, :uid, :tid, :amt, :type, :desc, NOW()
            ) RETURNING transaction_id, created_at
    """)

    ##amount co the la so duong(nap) hoac am(tru)
    #Journey Service gui so duong
    #neu la payment/penalty -> luu so am de hien mau do tren UI
    #neu la top_up -> luu so duong

    final_amount = req.amount
    if req.type in ["TICKET_PAYMENT", "PENALTY"] and final_amount > 0:
        final_amount = -final_amount

    row = db.execute(sql, {
        "id": new_id,
        "uid": req.user_id,
        "tid": req.ticket_id,
        "amt": final_amount,
        "type": req.type,
        "desc": req.description
    }).mappings().first()

    db.commit()

    return TransactionResponse(
        transaction_id = new_id,
        user_id= req.user_id,
        ticket_id = req.ticket_id,
        amount=final_amount,
        type= req.type,
        description=req.description,
        created_at=row["created_at"]
    )

@router.get("/internal/history", response_model= list[TransactionResponse])
def get_history(x_user_id: str = Header(None, alias="X-User-Id"), db: Session = Depends(get_db)):
    if not x_user_id:
        raise HTTPException(401, "User context missing")

    sql = text ("""
        SELECT * FROM transactions
        WHERE user_id = :uid
        ORDER BY created_at DESC
        LIMIT 50
    """)

    rows = db.execute(sql, {"uid": x_user_id}).mappings().all()


    return rows