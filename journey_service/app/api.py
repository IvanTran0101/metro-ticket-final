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
    GateRequest, GateResponse, PenaltyPaymentRequest,
    JourneyHistoryItem, TicketItem,
    PurchaseRequest, PurchaseResponse
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
        if req.ticket_type == "DAY":
            base_amount = 40000.0
            usage_limit = 100 #limit base for a Day
        elif req.ticket_type == "MONTH":
            base_amount = 200000.0
            usage_limit = 1000 #limit base for a Month
        else:
            # SINGLE / RETURN
            fare_data = sch_client.calculate_fare(req.from_station, req.to_station)
            base_amount = float(fare_data["total_amount"])
            if req.ticket_type == "RETURN":
                base_amount *= 2
                usage_limit = 2
            else:
                usage_limit = 1
                
    except Exception as e:
        raise HTTPException(400, f"Calculate fare failed: {e}")

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
        # check if balance not enough, send message to user, force them to contact supervisor to topup balance
        raise HTTPException(402, detail="Insufficient balance. Please contact supervisor to top up.")

    code = _generate_code()
    
    #create a ticket, insert the ticket into "tickets" table
    try:
        sql = text("""
            INSERT INTO tickets (ticket_id, user_id, ticket_code, ticket_type, fare_amount, origin_station_id, destination_station_id, status, remaining_trips, max_trips, valid_until)
            VALUES (:tid, :uid, :code, :type, :fare, :origin, :dest, 'ACTIVE', :rem, :max, NOW() + INTERVAL '1 day')
        """)
        
        ticket_id = str(uuid.uuid4())
        
        db.execute(sql, {
            "tid": ticket_id, 
            "uid": x_user_id,
            "code": code, 
            "type": req.ticket_type,
            "fare": final_amount,
            "origin": req.from_station if req.ticket_type in ["SINGLE", "RETURN"] else None,
            "dest": req.to_station if req.ticket_type in ["SINGLE", "RETURN"] else None,
            "rem": usage_limit,
            "max": usage_limit
        })
        db.commit()

        # Log transaction to Payment Service (History)
        try:
            PaymentClient().log_transaction(
                user_id=x_user_id,
                amount=final_amount,
                description=f"Purchase {req.ticket_type} Ticket",
                ticket_id=ticket_id
            )
        except Exception as e:
            print(f"Failed to log purchase transaction: {e}")

    except Exception as e:
        raise HTTPException(500, f"Database error: {e}")

    #return ticket code and final fare amount indicate successfully purchased
    return PurchaseResponse(journey_code = code, fare_amount = final_amount, message="SUCCESS")



@router.post("/gate/check-in", response_model=GateResponse)
def gate_check_in(req: GateRequest, db: Session = Depends(get_db)):
    #check if code exists
    sql_ticket = text("SELECT * FROM tickets WHERE ticket_code = :c")
    ticket = db.execute(sql_ticket, {"c": req.journey_code}).mappings().first()

    if not ticket: raise HTTPException(404,"Ticket not found")

    #check if code valid?
    if ticket["status"] != 'ACTIVE':
         raise HTTPException(400, f"Ticket is {ticket['status']}")

    if ticket["valid_until"] and ticket["valid_until"] < datetime.now(ticket["valid_until"].tzinfo):
         db.execute(text("UPDATE tickets SET status='EXPIRED' WHERE ticket_id=:id"), {"id": ticket["ticket_id"]})
         db.commit()
         raise HTTPException(400, "Ticket EXPIRED")
    
    if ticket["remaining_trips"] is not None and ticket["remaining_trips"] <= 0:
         raise HTTPException(400, "Ticket has no trips left")

    #validate station
    # SINGLE: Must check-in at Origin
    # RETURN: Must check-in at Origin or Destination 
    ticket_type = ticket["ticket_type"]
    origin = ticket["origin_station_id"]
    dest = ticket["destination_station_id"]

    if ticket_type == "SINGLE":
        if origin and req.station_id != origin:
             raise HTTPException(400, f"Wrong Station! Ticket valid from {origin} only.")
    
    elif ticket_type == "RETURN":
        #bind max_tríp = remaining trips at the first place then minus remaining_trips, 
        # if the 2 attribute or not the same any more thats means passenger arrived and comeback using the destination 
        if ticket["max_trips"] == ticket["remaining_trips"]:
             if origin and req.station_id != origin:
                 raise HTTPException(400, f"First leg must start at {origin}")
        else:
             if dest and req.station_id != dest:
                 raise HTTPException(400, f"Return leg must start at {dest}")

    #check if code is being used?
    sql_active = text("SELECT * FROM journeys WHERE ticket_id = :tid AND status = 'IN_PROGRESS'")
    active_journey = db.execute(sql_active, {"tid": ticket["ticket_id"]}).mappings().first()
    if active_journey:
         #deny
         raise HTTPException(400, "Ticket already used for entry. Please check out first.")

    #create journey now after validation
    try:
        # Decrement usage
        if ticket["remaining_trips"] is not None:
             db.execute(text("UPDATE tickets SET remaining_trips = remaining_trips - 1 WHERE ticket_id=:id"), {"id": ticket["ticket_id"]})
        
        # Insert Journey
        db.execute(text("""
            INSERT INTO journeys (journey_id, ticket_id, check_in_station_id, check_in_time, status)
            VALUES (:jid, :tid, :sid, NOW(), 'IN_PROGRESS')
        """), {
            "jid": str(uuid.uuid4()),
            "tid": ticket["ticket_id"],
            "sid": req.station_id
        })
        db.commit()

    except Exception as e:
         db.rollback()
         raise HTTPException(500, f"Check-in failed: {e}")

    return GateResponse(ok = True, message = f"Welcome at {req.station_id}")

@router.post("/gate/check-out")
def gate_check_out(req: GateRequest, db: Session = Depends(get_db)):
    
    # check for ticket
    sql_ticket = text("SELECT * FROM tickets WHERE ticket_code = :c")
    ticket = db.execute(sql_ticket, {"c": req.journey_code}).mappings().first()
    if not ticket: raise HTTPException(404, "Ticket not found")

    # check for active journey that has the same ticket id
    sql_journey = text("SELECT * FROM journeys WHERE ticket_id = :tid AND status = 'IN_PROGRESS'")
    journey = db.execute(sql_journey, {"tid": ticket["ticket_id"]}).mappings().first()

    # Case: No Active Journey found
    if not journey:
        # check if the journey has just finished
        sql_last = text("SELECT * FROM journeys WHERE ticket_id = :tid ORDER BY created_at DESC LIMIT 1")
        last = db.execute(sql_last, {"tid": ticket["ticket_id"]}).mappings().first()
        if last and last["status"] in ["COMPLETED", "CLOSED"]:
             raise HTTPException(400, "Journey already closed (Double Check-out?)")
        
        # Check-out without Check-in? (Penalty)
        raise HTTPException(400, "No ACTIVE journey found. Did you check in?")

    # 3. Existing Logic for Penalty/Fare calculation 
    #check same station exit (<15m)
    if journey["check_in_station_id"] == req.station_id:
        check_in_time = journey["check_in_time"]
        now = datetime.now(check_in_time.tzinfo) if check_in_time.tzinfo else datetime.now()
        duration_minutes = (now - check_in_time).total_seconds() / 60

        # Common Logic: Revert Usage (Give back 1 trip) if it's a countable ticket
        if ticket["remaining_trips"] is not None:
             db.execute(text("UPDATE tickets SET remaining_trips = remaining_trips + 1 WHERE ticket_id = :tid"), 
                {"tid": ticket["ticket_id"]})

        if duration_minutes <= 15:
             # Case 1: Early Exit (<15m) -> Free Cancellation
             db.execute(text("UPDATE journeys SET status ='CANCELLED', check_out_time= NOW(), check_out_station_id= :s WHERE journey_id = :id"),
                {"s": req.station_id, "id": journey["journey_id"]})
             db.commit()
             return GateResponse( ok = True, message= f"Trip Cancelled (Same station exit). Usage reverted.")
        else:
             # Case 2: Overstay (>15m) -> Penalty 5k, but Usage Reverted
             penalty_amount = 5000.0
             penalty_reason = f"Same Station Overstay > 15m ({int(duration_minutes)}m)"
             
             db.execute(text("""
                UPDATE journeys 
                SET status = 'PENALTY_DUE', 
                    penalty_amount = :p, 
                    penalty_reason = :r,
                    check_out_station_id = :s,
                    check_out_time = NOW()
                WHERE journey_id = :id
             """), 
             {"p": penalty_amount, "r": penalty_reason, "s": req.station_id, "id": journey["journey_id"]})
             db.commit()
             
             return JSONResponse(status_code = 402, content={
                "error": "PENALTY",
                "message": f"Penalty: {penalty_reason}. Amount: {penalty_amount:,.0f} VND. Ticket usage returned.",
                "penalty_amount": penalty_amount,
                "journey_code": req.journey_code
             })

    # PENALTY LOGIC
    penalty_amount = 0.0
    penalty_reasons = []

    # 1. Overstay
    check_in_time = journey["check_in_time"]
    if check_in_time:
        now = datetime.now(check_in_time.tzinfo)
        duration = (now - check_in_time).total_seconds() / 60
        if duration > 240:
            penalty_amount = 50000.0
            penalty_reasons.append(f"Overstay > 240m ({int(duration)}m)")

    # 2. Wrong Station
    ticket_type = ticket["ticket_type"]
    
    paid = float(ticket.get("fare_amount", 0) or 0)
    
    #check logic calculate real fare for single/return ticket
    if ticket_type in ["SINGLE", "RETURN"]:
        try:
            sch_client = SchedulerClient()
            acc_client = AccountClient()
            user_info = acc_client.get_me(str(ticket["user_id"]))
            p_type = user_info.get("passenger_type", "STANDARD")
            
            real_fare_data = sch_client.calculate_fare(journey["check_in_station_id"], req.station_id)
            base_real = float(real_fare_data["total_amount"])
            
            real_price = base_real
            if p_type == "STUDENT": real_price *= 0.5
            elif p_type == "ELDERLY": real_price = 0
            
            if real_price > paid:
                diff = real_price - paid
                if penalty_amount < 50000:
                    wrong_station_penalty = diff + 10000
                    penalty_amount = max(penalty_amount, wrong_station_penalty)
                    penalty_reasons.append(f"Fee Diff: {diff:,.0f}")

        except Exception as e:
            print(f"Wrong station check failed: {e}")

    # 3. Apply Penalty
    if penalty_amount > 0:
        reason_str = " & ".join(penalty_reasons)
        db.execute(text("""
                UPDATE journeys 
                SET status = 'PENALTY_DUE', 
                    penalty_amount = :p, 
                    penalty_reason = :r,
                    check_out_station_id = :s,
                    check_out_time = NOW()
                WHERE journey_id = :id
            """), 
            {"p": penalty_amount, "r": reason_str, "s": req.station_id, "id": journey["journey_id"]}
        )
        db.commit()
        return JSONResponse(status_code = 402, content={
            "error": "PENALTY",
            "message": f"Penalty: {reason_str}. Amount: {penalty_amount:,.0f} VND",
            "penalty_amount": penalty_amount,
            "journey_code": req.journey_code
        })

    # Finalize
    db.execute(
        text("UPDATE journeys SET status = 'COMPLETED', check_out_station_id= :s, check_out_time=NOW() WHERE journey_id= :id"), 
        {"s": req.station_id, "id": journey["journey_id"]}
    )
    db.commit()

    # Async logging
    try:
         
         final_fare = float(ticket.get("fare_amount", 0.0) or 0.0)
         NotificationClient().send_receipt(
            user_id=ticket["user_id"], 
            amount=final_fare,
            journey_code=ticket["ticket_code"]
        )
    except Exception as e:
        print(f"Async error: {e}")
    
    return GateResponse(ok = True, message="Thank you")

@router.post("/gate/pay-penalty")
def pay_penalty(req: PenaltyPaymentRequest, db: Session = Depends(get_db)):
    # 1. Look up Ticket
    sql_ticket = text("SELECT * FROM tickets WHERE ticket_code = :c")
    ticket = db.execute(sql_ticket, {"c": req.journey_code}).mappings().first()
    if not ticket: raise HTTPException(404, "Ticket not found")

    # 2. Look up Penalty Journey
    sql_journey = text("SELECT * FROM journeys WHERE ticket_id = :tid AND status = 'PENALTY_DUE'")
    journey = db.execute(sql_journey, {"tid": ticket["ticket_id"]}).mappings().first()
    
    if not journey: raise HTTPException(404, "No penalty due for this ticket")

    acc_client = AccountClient()
    user_id = ticket["user_id"]

    try:
        acc_client.deduct_balance(str(user_id), req.amount, "Penalty Payment")
        payment_status = "PAID"
        
        # Log to Payment Service
        try:
             PaymentClient().log_transaction(
                user_id=str(user_id),
                amount=req.amount,
                description=f"Penalty Payment for {req.journey_code}",
                ticket_id=str(ticket["ticket_id"]),
                transaction_type="PENALTY"
             )
        except Exception as e:
            print(f"Failed to log penalty: {e}")

    except Exception:
        # Insufficient balance -> manual paying, contact the supervisor and mark the ticket is closed
        payment_status = "SUPERVISOR_RESOLUTION"
    
    reason_note = ""
    if payment_status == "SUPERVISOR_RESOLUTION":
        reason_note = " (Manual/Supervisor)"

    db.execute(
        text("UPDATE journeys SET status='CLOSED', penalty_reason = penalty_reason || :note, check_out_time=NOW() WHERE journey_id=:id"),
        {"note": reason_note, "id": journey["journey_id"]}
    )
    db.commit()
    
    msg = "Paid. Open Gate." if payment_status == "PAID" else "Insufficient balance. Contact Supervisor to pay & exit."
    return {"ok": True, "message": msg}

# ---------------------------------------------------------
# 5. HISTORY & WALLET
# ---------------------------------------------------------
@router.get("/tickets", response_model=list[TicketItem])
def get_tickets(x_user_id: str = Header(None, alias="X-User-Id"), db: Session = Depends(get_db)):
    sql = text("SELECT * FROM tickets WHERE user_id = :uid ORDER BY created_at DESC")
    rows = db.execute(sql, {"uid": x_user_id}).mappings().all()
    return rows

@router.get("/history", response_model=list[JourneyHistoryItem])
def get_history(x_user_id: str = Header(None, alias="X-User-Id"), db: Session = Depends(get_db)):

    sql = text("""
        SELECT j.*, t.ticket_code as journey_code, t.fare_amount 
        FROM journeys j
        JOIN tickets t ON j.ticket_id = t.ticket_id
        WHERE t.user_id = :uid 
        ORDER BY j.created_at DESC 
        LIMIT 15
    """)
    rows = db.execute(sql, {"uid": x_user_id}).mappings().all()
    return rows
    

@router.post("/internal/cron/process-missing-checkouts")
def process_missing_checkouts(db: Session = Depends(get_db)):
    # Join tickets to get user_id
    sql = text("""
        SELECT j.*, t.user_id, t.ticket_code 
        FROM journeys j
        JOIN tickets t ON j.ticket_id = t.ticket_id
        WHERE j.status = 'IN_PROGRESS'
        AND j.check_in_time < NOW() - INTERVAL '1 day'
    """)
    stuck_tickets = db.execute(sql).mappings().all()

    count = 0
    acc_client = AccountClient()
    max_penalty = 50000.0

    for ticket in stuck_tickets:
        try:
            acc_client.deduct_balance(
                str(ticket["user_id"]),
                max_penalty,
                f"Penalty: Missing Check-out for ticket {ticket['ticket_code']}"
            )
            
            # Log Penalty Transaction
            try:
                PaymentClient().log_transaction(
                    user_id=str(ticket["user_id"]),
                    amount=max_penalty,
                    description=f"Auto-Penalty: Missing Check-out {ticket['ticket_code']}",
                    ticket_id=str(ticket["ticket_id"]),
                    transaction_type="PENALTY"
                )
            except Exception as e:
                print(f"Failed to log auto-penalty: {e}")

            db.execute(text("UPDATE journeys SET status= 'CLOSED', penalty_amount= :p, check_out_time = NOW() WHERE journey_id = :id"),
            {"p": max_penalty, "id": ticket["journey_id"]})
            count += 1
        except Exception as e:
            print(f"Failed to process ticket {ticket['ticket_code']}: {e}")
        
    db.commit()
    return {"ok": True, "processed_count": count, "message": f"Processed {count} stuck tickets"}