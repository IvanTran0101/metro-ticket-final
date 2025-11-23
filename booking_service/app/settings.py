import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    BOOKING_DATABASE_URL: str = os.getenv("BOOKING_DATABASE_URL", "postgresql://postgres:password@db_booking:5432/booking_db")
    DB_POOL_SIZE: int = 5
    DB_ECHO: bool = False
    
    # Service URLs
    SCHEDULER_SERVICE_URL: str = os.getenv("SCHEDULER_SERVICE_URL", "http://scheduler_service:8000")

settings = Settings()
