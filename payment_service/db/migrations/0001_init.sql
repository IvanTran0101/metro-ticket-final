-- payment_service/db/migrations/0001_init.sql

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS payments;

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID NOT NULL,
    
    -- Link tới Journey nếu là giao dịch trừ vé (có thể null nếu là nạp tiền)
    -- Link tới Ticket (thay vì Journey)
    ticket_id      UUID, 
    
    amount         NUMERIC(12, 2) NOT NULL, -- Âm là trừ, Dương là nạp
    type           VARCHAR(20) NOT NULL,    -- TICKET_PAYMENT, TOP_UP, PENALTY
    description    TEXT,
    
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);