import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    JOURNEY_DATABASE_URL: str = os.getenv("JOURNEY_DATABASE_URL", "postgresql://postgres:password@db_journey:5432/journey_db")
    DB_POOL_SIZE: int = 5
    DB_ECHO: bool = False
    
    # Service URLs
    SCHEDULER_SERVICE_URL: str = os.getenv("SCHEDULER_SERVICE_URL", "http://scheduler_service:8080")
    ACCOUNT_SERVICE_URL: str = os.getenv("ACCOUNT_SERVICE_URL", "http://account_service:8080")
    PAYMENT_SERVICE_URL: str = os.getenv("PAYMENT_SERVICE_URL", "http://payment_service:8080")
    NOTIFICATION_SERVICE_URL: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification_service:8080")

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
settings = Settings()
