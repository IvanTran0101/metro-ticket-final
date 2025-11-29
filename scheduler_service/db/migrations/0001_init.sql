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

-- Seed some data
INSERT INTO trips (trip_id, brand, from_station_name, to_station_name, date_departure, departure_time, capacity, remaining_seats, status, route_name, fare_per_seat)
VALUES 
('11111111-1111-1111-1111-111111111111', 'MetroExpress', 'Station A', 'Station B', '2025-12-01', '08:00:00', 100, 100, 'Scheduled', 'Route 1', 50000),
('22222222-2222-2222-2222-222222222222', 'MetroExpress', 'Station B', 'Station A', '2025-12-01', '10:00:00', 100, 50, 'Scheduled', 'Route 1', 50000),
('33333333-3333-3333-3333-333333333333', 'MetroExpress', 'Station A', 'Station C', '2025-12-01', '12:00:00', 80, 20, 'Scheduled', 'Route 2', 60000),
('44444444-4444-4444-4444-444444444444', 'CityBus', 'Station C', 'Station A', '2025-12-02', '09:30:00', 60, 60, 'Scheduled', 'Route 3', 45000),
('55555555-5555-5555-5555-555555555555', 'CityBus', 'Station A', 'Station B', '2025-12-02', '14:15:00', 100, 0, 'Cancelled', 'Route 1', 50000),
('66666666-6666-6666-6666-666666666666', 'RapidTransit', 'Station B', 'Station D', '2025-12-03', '07:45:00', 120, 89, 'Scheduled', 'Route 4', 75000),
('77777777-7777-7777-7777-777777777777', 'RapidTransit', 'Station D', 'Station B', '2025-12-03', '11:00:00', 120, 60, 'Scheduled', 'Route 4', 75000),
('88888888-8888-8888-8888-888888888888', 'MetroExpress', 'Station A', 'Station B', '2025-12-04', '15:30:00', 100, 96, 'Scheduled', 'Route 1', 52000),
('99999999-9999-9999-9999-999999999999', 'CityBus', 'Station C', 'Station D', '2025-12-04', '13:20:00', 90, 90, 'Scheduled', 'Route 5', 40000),
