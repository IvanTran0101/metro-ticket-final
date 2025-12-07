from fastapi import FastAPI
from journey_service.app.api import router
from journey_service.app.scheduler import start_scheduler

app = FastAPI(title="Journey Service")

app.include_router(router)

@app.on_event("startup")
def on_startup():
    start_scheduler()

@app.get("/health")
def health_check():
    return {"status": "ok"}
