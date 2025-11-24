from fastapi import FastAPI
from scheduler_service.app.api import router

app = FastAPI(title="Scheduler Service")

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
