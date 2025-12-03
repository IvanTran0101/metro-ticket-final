from fastapi import FastAPI

from journey_service.app.api import router

app = FastAPI(title="Journey Service")

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
