from __future__ import annotations
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # Web service
    SERVICE_HOST: str = Field(default="0.0.0.0")
    SERVICE_PORT: int = Field(default=8080)
    
    # Email (SMTP)
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="trananhm265@gmail.com")
    SMTP_PASSWORD: str = Field(default="mtaixgkchrxwjmrt")
    EMAIL_FROM: str = Field(default="trananhm265@gmail.com")
    
    # Testing
    DRY_RUN: bool = Field(default=False)

settings = Settings()
