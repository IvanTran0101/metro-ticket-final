from __future__ import annotations

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # Web server
    SERVICE_HOST: str = Field(default="0.0.0.0")
    SERVICE_PORT: int = Field(default=8080)

    # Database (SQLAlchemy URL for PostgreSQL recommended)
    ACCOUNT_DATABASE_URL: str = Field(
        default="postgresql+psycopg2://account_user:account_pass@localhost:5432/account_db",
        description="Connection string to the Account service database",
    )
    DB_POOL_SIZE: int = Field(default=10)
    DB_ECHO: bool = Field(default=False)

    
    # Business parameters
    HOLD_EXPIRES_MIN: int = Field(default=15, description="Minutes until a hold expires")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
