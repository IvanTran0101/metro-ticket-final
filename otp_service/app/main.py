import logging
import threading
from fastapi import FastAPI

from otp_service.app.api import router as api_router


logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    app = FastAPI(title="otp_service")
    app.include_router(api_router)

    return app


app = create_app()
