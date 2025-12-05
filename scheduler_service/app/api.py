from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta, time
import math
from scheduler_service.app.db import get_db
from scheduler_service.app.schemas import (
    MetroLine, Station,
    RouteSearchRequest, FareResponse,
    InternalFareRequest, InternalFareResponse,
    StationScheduleResponse, NextTrainInfo
)

router = APIRouter()
@router.get("/lines", response_model=list[MetroLine])
def get_lines(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM metro_lines ORDER BY line_id"))
    return result.mappings().all()

@router.get("/stations", response_model = list[Station])
def get_stations(line_id: str | None = None, db: Session = Depends(get_db)):

    if line_id:
        sql = text(
            """
            SELECT s.* FROM stations s
            JOIN line_stations ls ON s.station_id = ls.station_id
            WHERE ls.line_id = :lid AND s.is_active = true
            ORDER BY ls.station_order
        """
        )
        result = db.execute(sql,{"lid": line_id})
    else: 
        sql = text("SELECT * FROM stations WHERE is_active = true ORDER BY station_id")
        result = db.execute(sql)

    return result.mappings().all()

def _calculate_fare_logic(db: Session, from_station: str, to_station: str) -> dict:

    #tim tuyen chung va khoang cach giua 2 ga
    #logic: tim dong trong line_stations ma 2 ga cung thuoc 1 line
    sql_dist = text("""
        SELECT
            ls1.line_id,
            ABS(ls1.distance_km - ls2.distance_km) as distance,
            ABS(ls1.station_order - ls2.station_order) as stops
        FROM line_stations ls1
        JOIN line_stations ls2 ON ls1.line_id = ls2.line_id
        WHERE ls1.station_id = :s1 AND ls2.station_id = :s2
        LIMIT 1
    """)
    row = db.execute(sql_dist, {"s1": from_station, "s2": to_station}).mappings().first()

    if not row:
        raise HTTPException(404, "Can not found line between 2 stations")
    
    distance = float(row["distance"])

    rule = db.execute(text("SELECT * FROM fare_rules LIMIT 1")).mappings().first()
    if not rule:
        base_fare = 12000
        price_per_km = 2000
    else:
        base_fare = float(rule["base_fare"])
        price_per_km = float(rule["price_per_km"])

    total_fare = base_fare + (distance * price_per_km)

    total_fare = math.ceil(total_fare /1000) * 1000

    return {
        "distance": distance,
        "total_fare": total_fare,
        "base_fare": base_fare,
        "line_id": row["line_id"]
    }

@router.post("/routes/search", response_model=FareResponse)
def search_route(req: RouteSearchRequest, db: Session = Depends(get_db)):
    #lay ten ga hien thi
    s_info = db.execute(
        text("SELECT station_id, name FROM stations WHERE station_id IN (:s1, :s2)"),
        {"s1": req.from_station, "s2": req.to_station}
    ).mappings().all()

    s_map = {r["station_id"]: r["name"] for r in s_info}

    data = _calculate_fare_logic(db, req.from_station, req.to_station)

    est_time = int((data["distance"]/ 40 * 60) + 2)

    return FareResponse(
        from_station_name = s_map.get(req.from_station, req.from_station),
        to_station_name = s_map.get(req.to_station, req.to_station),
        distance_km = round(data["distance"], 1),
        standard_fare = data["total_fare"],
        estimated_time_mins = est_time,
        route_description = f"Moving on {data['line_id']}"
    )

@router.post("/internal/calculate-fare", response_model = InternalFareResponse)
def internal_caculate_fare(req: InternalFareRequest, db: Session = Depends(get_db)):

    data = _calculate_fare_logic(db, req.from_station, req.to_station)

    final_fare = data["total_fare"]
    if req.passenger_type == 'STUDENT':
        final_fare = final_fare * 0.5
    elif req.passenger_type == 'ELDERLY':
        final_fare = 0

    return InternalFareResponse(
        base_fare = data["base_fare"],
        distance_fare = data["total_fare"] - data["base_fare"],
        total_amount = final_fare,
        currency= "VND"
    )

@router.get("/stations/{station_id}/next-trains", response_model= StationScheduleResponse)
def get_next_trains(station_id: str, db: Session = Depends(get_db)):
    #lay ten ga

    st = db.execute(text("SELECT name FROM stations WHERE station_id = :sid"), {"sid": station_id}).mappings().first()
    if not st:
        raise HTTPException(404, "station not found")

    current_now = datetime.now()
    current_time_str = current_now.strftime("%H:%M:%S")
    print(f"DEBUG: Station {station_id}, Current Time: {current_now}")

    #query phuc tap: join schedule -> route -> route station de tinh gio den
    #cong thuc: gio den = gio khoi hanh (trip) + thoi gian di chuyen (route_station)
    sql = text(
        """
        SELECT 
            ml.name as line_name,
            r.description as direction_desc,
            ts.departure_time,
            ts.train_code,
            rs.travel_time_from_start
        FROM trip_schedules ts
        JOIN routes r ON ts.route_id = r.route_id
        JOIN route_stations rs ON r.route_id = rs.route_id
        JOIN metro_lines ml ON r.line_id = ml.line_id
        WHERE rs.station_id = :sid
        AND ts.is_active = true
        ORDER BY ts.departure_time
        """
    )
    rows = db.execute(sql, {"sid": station_id}).mappings().all()
    print(f"DEBUG: Found {len(rows)} raw schedules for station {station_id}")

    next_trains = []

    for row in rows:
        #tinh thoi gian tau den ga
        dep_time = row["departure_time"]
        travel_seconds = row["travel_time_from_start"]

        train_arrival_dt = datetime.combine(current_now.date(), dep_time) + timedelta(seconds=travel_seconds)

        if train_arrival_dt < current_now:
            continue
            
        diff = train_arrival_dt - current_now
        minutes_left = int(diff.total_seconds() / 60)

        if minutes_left > 60:
            continue

        next_trains.append(NextTrainInfo(
            line_name = row["line_name"],
            direction= row["direction_desc"],
            departure_time = train_arrival_dt.time(),
            minutes_left=minutes_left,
            train_code=row["train_code"]
        ))

        if len(next_trains) >= 3:
            continue
    
    return StationScheduleResponse(
        station_id = station_id,
        station_name= st["name"],
        current_time = current_time_str,
        next_trains = next_trains
    )