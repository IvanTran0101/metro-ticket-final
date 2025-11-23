import logging
from fastapi import FastAPI
import threading

from account_service.app.api import router as api_router

logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    app = FastAPI(title="account_service")
    app.include_router(api_router)

    return app


app = create_app()
