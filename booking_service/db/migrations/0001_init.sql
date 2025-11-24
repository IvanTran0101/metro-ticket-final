-- Booking Service initial schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS bookings (
    booking_id         uuid        PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id            uuid        NOT NULL,
    user_id            uuid        NOT NULL,
    seats              int         NOT NULL,
    seat_fare          numeric     NOT NULL,
    total_amount       numeric     NOT NULL,
    status             text        NOT NULL, -- 'Pending', 'Paid', 'Cancelled'
    booking_code       text        NOT NULL,
    payment_id         uuid,       -- Nullable initially, updated after payment
    created_at         timestamp   DEFAULT now(),
    paid_at            timestamp,
    cancelled_at       timestamp
);
