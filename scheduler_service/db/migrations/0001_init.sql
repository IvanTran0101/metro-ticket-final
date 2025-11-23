-- Scheduler Service initial schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS trips (
    trip_id            uuid        PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand              text        NOT NULL,
    from_station_name  text        NOT NULL,
    to_station_name    text        NOT NULL,
    date_departure     date        NOT NULL,
    departure_time     time        NOT NULL,
    capacity           int         NOT NULL,
    remaining_seats    int         NOT NULL,
    status             text        NOT NULL, -- 'Scheduled', 'Cancelled', 'Completed'
    route_name         text        NOT NULL,
    fare_per_seat      numeric     NOT NULL
);

CREATE TABLE IF NOT EXISTS seat_reservations (
    reservation_id     uuid        PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id            uuid        NOT NULL,
    seats_reserved     int         NOT NULL,
    status             text        NOT NULL, -- 'Locked', 'Confirmed', 'Cancelled'
    expires_at         timestamp   NOT NULL,
    created_at         timestamp   DEFAULT now()
);

-- Seed some data
INSERT INTO trips (trip_id, brand, from_station_name, to_station_name, date_departure, departure_time, capacity, remaining_seats, status, route_name, fare_per_seat)
VALUES 
('11111111-1111-1111-1111-111111111111', 'MetroExpress', 'Station A', 'Station B', '2025-12-01', '08:00:00', 100, 100, 'Scheduled', 'Route 1', 50000),
('22222222-2222-2222-2222-222222222222', 'MetroExpress', 'Station B', 'Station A', '2025-12-01', '10:00:00', 100, 50, 'Scheduled', 'Route 1', 50000);
