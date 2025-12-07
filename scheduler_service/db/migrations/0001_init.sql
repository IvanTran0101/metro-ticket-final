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
    train_code      VARCHAR(20), -- Mã đoàn tàu vật lý (VD: Hitachi-01)
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


INSERT INTO route_stations (route_id, station_id, stop_sequenece, travel_time_from_start) VALUES
(1, 'S01', 1, 0),      -- Xuất phát
(1, 'S02', 2, 120),    -- +2 phút
(1, 'S03', 3, 600),    -- +10 phút (2m đi + 5m nghỉ + 3m đi)
(1, 'S13', 4, 2400);   -- +40 phút (10m + 5m nghỉ + 25m đi)


INSERT INTO route_stations (route_id, station_id, stop_sequenece, travel_time_from_start) VALUES
(2, 'S13', 1, 0),
(2, 'S03', 2, 1500),   -- 25 phút
(2, 'S02', 3, 1980),   -- 33 phút (25m đi + 5m nghỉ + 3m đi)
(2, 'S01', 4, 2400);   -- 40 phút (33m + 5m nghỉ + 2m đi)

INSERT INTO trip_schedules (trip_id, route_id, departure_time, train_code, is_active) VALUES
('T_R1_01_0800', 1, '08:00:00', 'Hitachi-01', true),
('T_R2_01_0845', 2, '08:45:00', 'Hitachi-01', true),
('T_R1_01_0930', 1, '09:30:00', 'Hitachi-01', true),
('T_R2_01_1015', 2, '10:15:00', 'Hitachi-01', true),
('T_R1_01_1100', 1, '11:00:00', 'Hitachi-01', true),
('T_R2_01_1145', 2, '11:45:00', 'Hitachi-01', true),
('T_R1_01_1230', 1, '12:30:00', 'Hitachi-01', true),
('T_R2_01_1315', 2, '13:15:00', 'Hitachi-01', true),
('T_R1_01_1400', 1, '14:00:00', 'Hitachi-01', true),
('T_R2_01_1445', 2, '14:45:00', 'Hitachi-01', true),
('T_R1_01_1530', 1, '15:30:00', 'Hitachi-01', true),
('T_R2_01_1615', 2, '16:15:00', 'Hitachi-01', true),
('T_R1_02_0810', 1, '08:10:00', 'Hitachi-02', true),
('T_R2_02_0855', 2, '08:55:00', 'Hitachi-02', true),
('T_R1_02_0940', 1, '09:40:00', 'Hitachi-02', true),
('T_R2_02_1025', 2, '10:25:00', 'Hitachi-02', true),
('T_R1_02_1110', 1, '11:10:00', 'Hitachi-02', true),
('T_R2_02_1155', 2, '11:55:00', 'Hitachi-02', true),
('T_R1_02_1240', 1, '12:40:00', 'Hitachi-02', true),
('T_R2_02_1325', 2, '13:25:00', 'Hitachi-02', true),
('T_R1_02_1410', 1, '14:10:00', 'Hitachi-02', true),
('T_R2_02_1455', 2, '14:55:00', 'Hitachi-02', true),
('T_R1_02_1540', 1, '15:40:00', 'Hitachi-02', true),
('T_R2_02_1625', 2, '16:25:00', 'Hitachi-02', true),
('T_R1_03_0820', 1, '08:20:00', 'Hitachi-03', true),
('T_R2_03_0905', 2, '09:05:00', 'Hitachi-03', true),
('T_R1_03_0950', 1, '09:50:00', 'Hitachi-03', true),
('T_R2_03_1035', 2, '10:35:00', 'Hitachi-03', true),
('T_R1_03_1120', 1, '11:20:00', 'Hitachi-03', true),
('T_R2_03_1205', 2, '12:05:00', 'Hitachi-03', true),
('T_R1_03_1250', 1, '12:50:00', 'Hitachi-03', true),
('T_R2_03_1335', 2, '13:35:00', 'Hitachi-03', true),
('T_R1_03_1420', 1, '14:20:00', 'Hitachi-03', true),
('T_R2_03_1505', 2, '15:05:00', 'Hitachi-03', true),
('T_R1_03_1550', 1, '15:50:00', 'Hitachi-03', true),
('T_R2_03_1635', 2, '16:35:00', 'Hitachi-03', true),
('T_R1_04_0830', 1, '08:30:00', 'Hitachi-04', true),
('T_R2_04_0915', 2, '09:15:00', 'Hitachi-04', true),
('T_R1_04_1000', 1, '10:00:00', 'Hitachi-04', true),
('T_R2_04_1045', 2, '10:45:00', 'Hitachi-04', true),
('T_R1_04_1130', 1, '11:30:00', 'Hitachi-04', true),
('T_R2_04_1215', 2, '12:15:00', 'Hitachi-04', true),
('T_R1_04_1300', 1, '13:00:00', 'Hitachi-04', true),
('T_R2_04_1345', 2, '13:45:00', 'Hitachi-04', true),
('T_R1_04_1430', 1, '14:30:00', 'Hitachi-04', true),
('T_R2_04_1515', 2, '15:15:00', 'Hitachi-04', true),
('T_R1_04_1600', 1, '16:00:00', 'Hitachi-04', true),
('T_R2_04_1645', 2, '16:45:00', 'Hitachi-04', true),
('T_R1_05_0840', 1, '08:40:00', 'Hitachi-05', true),
('T_R2_05_0925', 2, '09:25:00', 'Hitachi-05', true),
('T_R1_05_1010', 1, '10:10:00', 'Hitachi-05', true),
('T_R2_05_1055', 2, '10:55:00', 'Hitachi-05', true),
('T_R1_05_1140', 1, '11:40:00', 'Hitachi-05', true),
('T_R2_05_1225', 2, '12:25:00', 'Hitachi-05', true),
('T_R1_05_1310', 1, '13:10:00', 'Hitachi-05', true),
('T_R2_05_1355', 2, '13:55:00', 'Hitachi-05', true),
('T_R1_05_1440', 1, '14:40:00', 'Hitachi-05', true),
('T_R2_05_1525', 2, '15:25:00', 'Hitachi-05', true),
('T_R1_05_1610', 1, '16:10:00', 'Hitachi-05', true),
('T_R2_05_1655', 2, '16:55:00', 'Hitachi-05', true);