-- Booking Service initial schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS journeys (
    journey_id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID NOT NULL,

    journey_code            VARCHAR(10) UNIQUE NOT NULL,

    check_in_station_id     VARCHAR(10) NOT NULL,
    check_in_time           TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    check_out_station_id    VARCHAR(10),
    check_out_time          TIMESTAMP WITH TIME ZONE,

    fare_amount             NUMERIC(12,2) DEFAULT 0,
    penalty_amount          NUMERIC(12,2) DEFAULT 0,
    penalty_reason          VARCHAR(50),

    status                  VARCHAR(20) NOT NULL DEFAULT 'IN_PROGRESS', -- IN_PROGRESS, COMPLETED, PENALTY_DUE, CLOSED

    created_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_active_journey ON journeys(user_id) WHERE status = 'IN_PROGRESS';
CREATE INDEX idx_journey_code ON journeys(journey_code);