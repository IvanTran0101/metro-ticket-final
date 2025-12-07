-- Account Service initial schema (PostgreSQL)
-- Recreated migration: accounts and holds tables

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- accounts: user profiles + current balance
CREATE TABLE IF NOT EXISTS accounts (
    user_id        uuid        PRIMARY KEY DEFAULT uuid_generate_v4(),
    password_hash  text        NOT NULL,
    balance        numeric(12,2)     DEFAULT 0,
    username       text        NOT NULL UNIQUE,
    full_name      text        NOT NULL,
    phone_number   text        NOT NULL,
    email          text        NOT NULL UNIQUE,
    passenger_type varchar(20) DEFAULT 'STANDARD' -- STANDARD, STUDENT, ELDERLY
);

