import logging
import sys
import threading
from fastapi import FastAPI

logger = logging.getLogger("notification_service")
logger.setLevel(logging.INFO)

# Reuse uvicorn handlers when available, otherwise fall back to stdout.
uvicorn_logger = logging.getLogger("uvicorn.error")
if uvicorn_logger.handlers:
    for handler in uvicorn_logger.handlers:
        logger.addHandler(handler)
else:
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    logger.addHandler(stream_handler)


def create_app() -> FastAPI:
    app = FastAPI(title="notification_service")

    return app


app = create_app()
