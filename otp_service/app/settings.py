from __future__ import annotations
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # OTP params
    OTP_TTL_SEC: int = Field(default=300)  # 5 minutes
    OTP_LENGTH: int = Field(default=6)

    # Redis cache
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    REDIS_POOL_SIZE: int = Field(default=10)

    # Service URLs
    NOTIFICATION_SERVICE_URL: str = Field(default="http://notification_service:8080")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
