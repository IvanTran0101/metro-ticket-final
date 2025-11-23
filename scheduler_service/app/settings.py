import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    SCHEDULER_DATABASE_URL: str = os.getenv("SCHEDULER_DATABASE_URL", "postgresql://postgres:password@db_scheduler:5432/scheduler_db")
    DB_POOL_SIZE: int = 5
    DB_ECHO: bool = False

settings = Settings()
