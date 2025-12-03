-- Scheduler Service initial schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS metro_lines (
    line_id     VARCHAR(10) PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    code        VARCHAR(20),
    color       VARCHAR(10) DEFAULT '#000000',
    status      VARCHAR(20) DEFAULT 'OPERATIONAL'
);

CREATE TABLE IF NOT EXISTS stations(
    station_id  VARCHAR(10) PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    address     TEXT,
    lat         FLOAT,
    long        FLOAT,
    is_active   BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS line_stations (
    line_id         VARCHAR(10) REFERENCES metro_lines(line_id),
    station_id      VARCHAR(10) REFERENCES stations(station_id),
    distance_km     FLOAT NOT NULL,
    station_order   INT,
    PRIMARY KEY (line_id,station_id)
);

CREATE TABLE IF NOT EXISTS routes (
    route_id    SERIAL PRIMARY KEY,
    line_id     VARCHAR(10) REFERENCES metro_lines(line_id),
    direction   INT NOT NULL, -- direction 0: di (inbound), 1: ve(outbound)
    description VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS route_stations (
    route_id               INT REFERENCES routes(route_id),
    station_id             VARCHAR(10) REFERENCES stations(station_id),
    stop_sequenece         INT NOT NULL,
    travel_time_from_start INT, --use second to count the arrival time
    PRIMARY KEY (route_id, station_id)
);

CREATE TABLE IF NOT EXISTS trip_schedules (
    trip_id         VARCHAR(50) PRIMARY KEY,
    route_id        INT REFERENCES routes(route_id),
    departure_time  TIME NOT NULL,
    days_of_week    VARCHAR(7) DEFAULT '1111111',
    is_active       BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS fare_rules (
    id               SERIAL PRIMARY KEY,
    base_fare        NUMERIC DEFAULT 12000,
    price_per_km     NUMERIC DEFAULT 2000,
    min_balance      NUMERIC DEFAULT 20000,
    max_travel_time  INT DEFAULT 120,
    overstay_penalty NUMERIC DEFAULT 50000
);

-- Line 1
INSERT INTO metro_lines VALUES ('L01', 'Bến Thành - Suối Tiên', 'Line 1', '#FF0000');

-- Các ga chính
INSERT INTO stations (station_id, name) VALUES 
('S01', 'Bến Thành'),
('S02', 'Nhà hát Thành phố'),
('S03', 'Ba Son'),
('S13', 'Suối Tiên');

-- Gán ga vào Line 1 với khoảng cách
INSERT INTO line_stations (line_id, station_id, distance_km, station_order) VALUES
('L01', 'S01', 0.0, 1),
('L01', 'S02', 0.6, 2),
('L01', 'S03', 2.3, 3),
('L01', 'S13', 19.7, 13);

-- Tạo 2 lộ trình mẫu
INSERT INTO routes (route_id, line_id, direction, description) VALUES
(1, 'L01', 0, 'Bến Thành đi Suối Tiên'),
(2, 'L01', 1, 'Suối Tiên về Bến Thành');

-- Bảng giá
INSERT INTO fare_rules (base_fare, price_per_km, min_balance) VALUES (12000, 2000, 20000);