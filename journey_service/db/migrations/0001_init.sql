-- Booking Service initial schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Bảng TICKETS: Quản lý Quyền đi lại (Entitlement)
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL,      -- Người sở hữu vé
    
    ticket_code         VARCHAR(20) UNIQUE NOT NULL, -- Mã QR cố định cho vé này
    ticket_type         VARCHAR(20) NOT NULL, -- SINGLE, RETURN, DAY, MONTH
    
    fare_amount         NUMERIC(12,2) DEFAULT 0,
    
    origin_station_id   VARCHAR(10), -- Thêm để validate luồng đi
    destination_station_id VARCHAR(10),

    status              VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, EXPIRED, USED
    
    remaining_trips     INT,                 -- NULL = Unlimited (Tháng/Ngày), Số = Lượt còn lại
    max_trips           INT,                 -- Tổng số lượt cho phép (để track)
    
    valid_from          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_until         TIMESTAMP WITH TIME ZONE, -- Hạn sử dụng (VD: Hết ngày 23:59)
    
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Bảng JOURNEYS: Lịch sử đi lại (Usage)
CREATE TABLE IF NOT EXISTS journeys (
    journey_id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id               UUID NOT NULL REFERENCES tickets(ticket_id), -- Link về vé nào
    
    check_in_station_id     VARCHAR(10) NOT NULL,
    check_in_time           TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    check_out_station_id    VARCHAR(10),
    check_out_time          TIMESTAMP WITH TIME ZONE,

    -- fare_amount Removed as it is redundant with tickets.fare_amount (for now)
    penalty_amount          NUMERIC(12,2) DEFAULT 0,
    penalty_reason          VARCHAR(255),

    status                  VARCHAR(20) NOT NULL DEFAULT 'IN_PROGRESS', -- IN_PROGRESS, COMPLETED, PENALTY_DUE, CLOSED

    created_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ticket_user ON tickets(user_id);
CREATE INDEX idx_ticket_code ON tickets(ticket_code);
CREATE INDEX idx_journey_ticket ON journeys(ticket_id);
-- Tìm chuyến đang đi dở của 1 vé
CREATE INDEX idx_active_journey ON journeys(ticket_id) WHERE status = 'IN_PROGRESS';