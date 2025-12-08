
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS payments;

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID NOT NULL,
    
   
    ticket_id      UUID, 
    
    amount         NUMERIC(12, 2) NOT NULL, 
    type           VARCHAR(20) NOT NULL,    
    description    TEXT,
    
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);