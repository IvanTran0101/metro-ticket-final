from string import ascii_uppercase
import uuid
import random
import string
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from journey_service.app.db import get_db
from journey_service.app.schemas import (
    PurchaseRequest, PurchaseResponse,
    GateRequest, GateResponse, PenaltyPaymentRequest,
    JourneyHistoryItem
)
from journey_service.app.clients.scheduler_client import SchedulerClient
from journey_service.app.clients.account_client import AccountClient
from journey_service.app.clients.payment_client import PaymentClient
from journey_service.app.clients.notification_client import NotificationClient

router = APIRouter()

def _generate_code():
    return ''.join(random.choices(ascii_uppercase + string.digits, k = 6))

@router.post("/ticket/purchase", response_model = PurchaseResponse)
def purchase_ticket(
    req: PurchaseRequest,
    x_user_id: str = Header(None, alias= "X-User-Id"),
    db: Session = Depends(get_db)
):
    if not x_user_id:
        raise HTTPException(401, "Unauthorized")

    sch_client= SchedulerClient()

    try:
        fare_data = sch_client.calculate_fare(req.from_station, req.to_station)
        base_amount = float(fare_data["total_amount"])
    except Exception as e:
        raise HTTPException(400, f"Calculate faid: {e}")

    acc_client = AccountClient()
    try:
        user_info = acc_client.get_me(x_user_id)
        p_type = user_info.get("passenger_type", "STANDARD")
        
        final_amount = base_amount
        if p_type == "STUDENT":
            final_amount = base_amount * 0.5
        elif p_type == "ELDERLY":
            final_amount = 0

        if final_amount >  0:
            acc_client.deduct_balance(x_user_id, final_amount, f"Buy ticket {req.from_station} -> {req.to_station}")

    except Exception as e:
        raise HTTPException(402, f"Payment failed: {e}")

    code = _generate_code()
    sql = text("""
        INSERT INTO journeys (journey_id, user_id, journey_code, check_in_station_id, fare_amount, status)
        VALUES (:jid, :uid, :code, :start, :fare, 'PAID')
    """)
    db.execute(sql, {
        "jid": str(uuid.uuid4()), "uid": x_user_id,
        "code": code, "start": req.from_station, "fare": final_amount
    })

    db.commit()

    return PurchaseResponse(journey_code = code, fare_amount = final_amount, message="SUCCESS")



@router.post("/gate/check-in", response_model=GateResponse)
def gate_check_in(req: GateRequest, db: Session = Depends(get_db)):
    sql = text("SELECT * FROM journeys WHERE journey_code = :c")
    ticket = db.execute(sql, {"c": req.journey_code}).mappings().first()

    if not ticket: raise HTTPException(404,"Code not exists")

    if ticket["status"] != "PAID":
        status_map = {"IN_TRANSIT": "TICKET IS BEING USED", "COMPLETED": "TICKET IS EXPIRED", "CLOSED": "TICKET IS CLOSED"}
        raise HTTPException(400, status_map.get(ticket["status"], "TICKET INVALID"))

    if ticket["check_in_station_id"] != req.station_id:
        raise HTTPException(400, f"WRONG GATE ! THIS TICKET MUST BE USED AT {ticket['check_in_station_id']}")

    db.execute(
        text("UPDATE journeys SET status= 'IN_TRANSIT', check_in_time=NOW() WHERE journey_id = :id "),
        {"id": ticket["journey_id"]}
    )
    db.commit()

    return GateResponse(ok = True, message= f"Welcome at {req.station_id}")

@router.post("/gate/check-out")
def gate_check_out(req: GateRequest, db: Session = Depends(get_db)):
    sql = text("SELECT * FROM journeys WHERE journey_code = :c")
    ticket = db.execute(sql, {"c": req.journey_code}).mappings().first()

    if not ticket: raise HTTPException(404, "Code not exists")
    if ticket["status"] != "IN_TRANSIT": raise HTTPException(400, "TICKET not check-in yet")

    #kiem tra di lo
    #tinh tien thuc te chang da di
    acc_client = AccountClient()
    p_type = "STANDARD"
    try: 
        user_info = acc_client.get_me(str(ticket["user_id"]))
        p_type = user_info.get("passenger_type", "STANDARD")
    except Exception as e:
        print(f"WARNING: could not fetch user info {e}")


    sch_client = SchedulerClient()

    try:
        real_fare = sch_client.calculate_fare(ticket["check_in_station_id"], req.station_id, passenger_type = p_type)
        real_price = float(real_fare["total_amount"])

        #lay lai account de check giam gia
        paid = float(ticket["fare_amount"])
        if real_price > paid:
            diff = real_price - paid
            penalty = diff + 10000

        db.execute(text("UPDATE journeys SET status= 'PENALTY_DUE' WHERE journey_id= :id"), {"id": ticket["journey_id"]})
        db.commit()

        return JSONResponse(status_code= 402, content={
            "error": "WRONG_DESTINATION",
            "message": f"YOU ARRIVED AT WRONG GATE! PLEASE PAY PENALTY {penalty:,.0f}vnd", 
            "penalty_amount": penalty,
            "journey_code": req.journey_code
        })
    except Exception as e:
        print(f"Warning check price: {e}")

    
    #logic kiem tra qua gio
    check_in_time = ticket["check_in_time"]
    if check_in_time:

        now = datetime.now(check_in_time.tzinfo)
        duration = (now - check_in_time).total_seconds() / 60
        if duration > 120:
            penalty = 50000
            db.execute("UPDATE journeys SET status= 'PENALTY_DUE' WHERE journey_id= :id", {"id": ticket["journey_id"]})
            db.commit()
            return JSONResponse(status_code = 402, content={
                "error": "OVERSTAY",
                "message": f"Staying at station over 120 mins ({int(duration)} mins). Penalty {penalty:,0f}vnd",
                "penalty_amount": penalty,
                "journey_code": req.journey_code
            })

    _finalize_journey(db,ticket, req.station_id)
    return GateResponse(ok = True, message="Thank you")

def _finalize_journey(db, ticket, end_station):
    db.execute(
        text("UPDATE journeys SET status = 'COMPLETED', check_out_station_id= :s, check_out_time=NOW() WHERE journey_id= :id"), {"s": end_station, "id": ticket["journey_id"]}

    )
    db.commit()

    try:
        PaymentClient().log_transaction(ticket["user_id"], float(ticket["fare_amount"]), "Vé hoàn tất")
        
        # [UPDATE] Truyền thêm journey_code vào để email đẹp hơn
        NotificationClient().send_receipt(
            user_id=ticket["user_id"], 
            amount=float(ticket["fare_amount"]),
            journey_code=ticket["journey_code"]
        )
    except Exception as e:
        print(f"Async error: {e}")

@router.post("/gate/pay-penalty")
def pay_penalty(req: PenaltyPaymentRequest, db: Session = Depends(get_db)):
    sql = text("SELECT * FROM journeys WHERE journey_code = :c")
    ticket = db.execute(sql, {"c": req.journey_code}).mappings().first()
    if not ticket: raise HTTPException(404, "Vé đâu?")

    acc_client = AccountClient()
    user_id = ticket["user_id"]

    try:
        # Thử trừ tiền
        acc_client.deduct_balance(user_id, req.amount, "Phí phạt Metro")
    except Exception:
        # Nếu trừ thất bại (do thiếu tiền)
        if req.auto_topup:
            # Logic: Nạp vừa đủ để trả (hoặc nạp chẵn 50k)
            # Ở đây ta giả lập nạp đúng số tiền phạt để đi qua
            acc_client.top_up(user_id, req.amount)
            # Trừ lại lần nữa
            acc_client.deduct_balance(user_id, req.amount, "Phí phạt Metro (Sau khi nạp)")
        else:
            # Báo lỗi để Frontend hiện nút Nạp
            raise HTTPException(402, detail="Thiếu tiền")

    # Mở cổng
    db.execute(
        text("UPDATE journeys SET status='CLOSED', penalty_amount=:p, check_out_time=NOW() WHERE journey_id=:id"),
        {"p": req.amount, "id": ticket["journey_id"]}
    )
    db.commit()
    
    return {"ok": True, "message": "Đã thanh toán phí phạt. Mời ra."}

# ---------------------------------------------------------
# 5. LỊCH SỬ
# ---------------------------------------------------------
@router.get("/history", response_model=list[JourneyHistoryItem])
def get_history(x_user_id: str = Header(None, alias="X-User-Id"), db: Session = Depends(get_db)):
    sql = text("SELECT * FROM journeys WHERE user_id = :uid ORDER BY created_at DESC")
    rows = db.execute(sql, {"uid": x_user_id}).mappings().all()
    return rows
    