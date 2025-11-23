from fastapi import FastAPI

from booking_service.app.api import router

app = FastAPI(title="Booking Service")

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
