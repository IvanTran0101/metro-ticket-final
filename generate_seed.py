from datetime import datetime, timedelta

trains = ["Hitachi-01", "Hitachi-02", "Hitachi-03", "Hitachi-04", "Hitachi-05"]
base_time = datetime(2024, 1, 1, 8, 0, 0)
headway = timedelta(minutes=10)

# Route 1: 40 mins travel. Route 2: 40 mins travel. Turnaround: 5 mins.
leg_duration = timedelta(minutes=40)
turnaround = timedelta(minutes=5)

sql_values = []

for i, train in enumerate(trains):
    # Each train starts 10 mins after the previous one
    current_time = base_time + (headway * i)
    
    # Generate 6 round trips (enough for 8am to ~5pm)
    for cycle in range(6):
        # --- Leg 1 (Route 1: Ben Thanh -> Suoi Tien) ---
        trip_id = f"T_R1_{train.split('-')[1]}_{current_time.strftime('%H%M')}"
        sql_values.append(f"('{trip_id}', 1, '{current_time.strftime('%H:%M:%S')}', '{train}', true)")
        
        # Arrive at Dest (T+40). Rest 5 mins. Depart T+45.
        current_time += leg_duration + turnaround
        
        # --- Leg 2 (Route 2: Suoi Tien -> Ben Thanh) ---
        trip_id = f"T_R2_{train.split('-')[1]}_{current_time.strftime('%H%M')}"
        sql_values.append(f"('{trip_id}', 2, '{current_time.strftime('%H:%M:%S')}', '{train}', true)")
        
        # Arrive at Start (T+45+40). Rest 5 mins. Depart T+90 (Next Cycle)
        current_time += leg_duration + turnaround

print("INSERT INTO trip_schedules (trip_id, route_id, departure_time, train_code, is_active) VALUES")
print(",\n".join(sql_values) + ";")
