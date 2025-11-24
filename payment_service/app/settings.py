from __future__ import annotations

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # Web server
    SERVICE_HOST: str = Field(default="0.0.0.0")
    SERVICE_PORT: int = Field(default=8080)

    # Database (SQLAlchemy URL for PostgreSQL recommended)
    PAYMENT_DATABASE_URL: str = Field(
        default="postgresql+psycopg2://payment_user:payment_pass@localhost:5432/payment_db",
        description="Connection string to the Payment service database",
    )
    DB_POOL_SIZE: int = Field(default=10)
    DB_ECHO: bool = Field(default=False)

    # Redis (payment intent cache)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_POOL_SIZE: int = Field(default=10)
   
    # Business parameters
    HOLD_EXPIRES_MIN: int = Field(default=15, description="Minutes until a hold expires")

    # Service URLs
    ACCOUNT_SERVICE_URL: str = Field(default="http://account_service:8080")
    OTP_SERVICE_URL: str = Field(default="http://otp_service:8080")
    BOOKING_SERVICE_URL: str = Field(default="http://booking_service:8080")
    SCHEDULER_SERVICE_URL: str = Field(default="http://scheduler_service:8080")
    NOTIFICATION_SERVICE_URL: str = Field(default="http://notification_service:8080")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
