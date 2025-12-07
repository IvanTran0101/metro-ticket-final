from __future__ import annotations

import uuid
from typing import Dict, Iterable, Optional

import httpx
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from libs.security.jwt import verify_and_decode
from gateway.app.settings import settings


HOP_BY_HOP_HEADERS: set[str] = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

ACCOUNT_URL = settings.ACCOUNT_SERVICE_URL.rstrip("/")
PAYMENT_URL = settings.PAYMENT_SERVICE_URL.rstrip("/")
TUITION_URL = settings.TUITION_SERVICE_URL.rstrip("/")
OTP_URL = settings.OTP_SERVICE_URL.rstrip("/")
NOTIF_URL = settings.NOTIFICATION_SERVICE_URL.rstrip("/")
AUTH_URL = settings.AUTHENTICATION_SERVICE_URL.rstrip("/")
JOURNEY_URL = settings.JOURNEY_SERVICE_URL.rstrip("/")
SCHEDULER_URL = settings.SCHEDULER_SERVICE_URL.rstrip("/")


app = FastAPI(title="Gateway")

# Configure CORS from settings
origins_cfg = settings.CORS_ALLOW_ORIGINS
origins = ["*"] if origins_cfg.strip() == "*" else [o.strip() for o in origins_cfg.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

from gateway.app.middleware import IdempotencyMiddleware
app.add_middleware(IdempotencyMiddleware, redis_url=settings.REDIS_URL)


_client: httpx.AsyncClient | None = None


@app.on_event("startup")
async def _startup() -> None:
    global _client
    _client = httpx.AsyncClient(timeout=httpx.Timeout(settings.HTTP_TIMEOUT))


@app.on_event("shutdown")
async def _shutdown() -> None:
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        finally:
            _client = None


def _filtered_headers(headers: Iterable[tuple[str, str]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in headers:
        lk = k.lower()
        if lk in HOP_BY_HOP_HEADERS or lk == "host":
            continue
        out[k] = v
    return out


async def _require_user(request: Request) -> str:
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = auth.split(" ", 1)[1].strip()
    try:
        claims = verify_and_decode(token, key=settings.JWT_SECRET, alg=settings.JWT_ALG)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = str(claims.get("sub") or "").strip()
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    return user_id


async def _proxy(request: Request, base_url: str, tail: str, *, require_auth: bool = True, method: Optional[str] = None) -> Response:
    global _client
    assert _client is not None

    # Allow unauthenticated access to service docs/openapi endpoints
    normalized_tail = (tail or "").lstrip("/")
    is_docs = (
        request.method.upper() == "GET"
        and (
            normalized_tail == "docs"
            or normalized_tail.startswith("docs/")
            or normalized_tail == "redoc"
            or normalized_tail.endswith("openapi.json")
        )
    )

    x_user_id = None
    x_user_email = None
    if require_auth and not is_docs:
        x_user_id = await _require_user(request)
        # Extract email from token for downstream services
        auth = request.headers.get("authorization") or ""
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
            try:
                claims = verify_and_decode(token, key=settings.JWT_SECRET, alg=settings.JWT_ALG)
                x_user_email = claims.get("email") or None
            except Exception:
                pass

    cid = request.headers.get("correlation-id") or str(uuid.uuid4())

    # Build outgoing headers
    upstream_url = f"{base_url}/{normalized_tail}"
    headers = _filtered_headers(request.headers.items()) # Assuming _filter_headers was a typo and _filtered_headers is intended
    headers["correlation-id"] = cid
    if x_user_id:
        headers["X-User-Id"] = x_user_id
    if x_user_email:
        headers["X-User-Email"] = x_user_email

    # Forward request
    try:
        body_bytes = await request.body()
        resp = await _client.request(
            method=request.method,
            url=upstream_url,
            headers=headers,
            params=dict(request.query_params),
            content=body_bytes,
            timeout=None,
        )
    except httpx.RequestError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Upstream unavailable")

    # Build response, filter hop-by-hop headers
    resp_headers = {k: v for k, v in resp.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}
    return Response(content=resp.content, status_code=resp.status_code, headers=resp_headers, media_type=resp.headers.get("content-type"))


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


# ---- Explicit reverse-proxy endpoints (as requested) ----



# ... (Phần đầu giữ nguyên)

# ---- CẬP NHẬT CÁC ROUTE MỚI ----

# 1. Scheduler (Hạ tầng & Giá)
@app.get("/scheduler/stations")
async def get_stations(request: Request) -> Response:
    return await _proxy(request, SCHEDULER_URL, "stations", require_auth=False)

@app.get("/scheduler/lines")
async def get_lines(request: Request) -> Response:
    return await _proxy(request, SCHEDULER_URL, "lines", require_auth=False)

@app.post("/scheduler/routes/search")
async def search_route(request: Request) -> Response:
    return await _proxy(request, SCHEDULER_URL, "routes/search", require_auth=True)

@app.get("/scheduler/stations/{station_id}/next-trains")
async def next_trains(station_id: str, request: Request) -> Response:
    return await _proxy(request, SCHEDULER_URL, f"stations/{station_id}/next-trains", require_auth=True)

# 2. Journey & Ticket (Thay thế Booking cũ)
@app.post("/booking/ticket/purchase")
async def purchase_ticket(request: Request) -> Response:
    return await _proxy(request, JOURNEY_URL, "ticket/purchase", require_auth=True)

@app.get("/booking/history")
async def journey_history(request: Request) -> Response:
    return await _proxy(request, JOURNEY_URL, "history", require_auth=True)

@app.get("/booking/tickets")
async def get_tickets(request: Request) -> Response:
    return await _proxy(request, JOURNEY_URL, "tickets", require_auth=True)

# 3. Gate Simulator (Cổng soát vé)
@app.post("/booking/gate/check-in")
async def gate_check_in(request: Request) -> Response:
    return await _proxy(request, JOURNEY_URL, "gate/check-in", require_auth=False)

@app.post("/booking/gate/check-out")
async def gate_check_out(request: Request) -> Response:
    return await _proxy(request, JOURNEY_URL, "gate/check-out", require_auth=False)

@app.post("/booking/gate/pay-penalty")
async def pay_penalty(request: Request) -> Response:
    return await _proxy(request, JOURNEY_URL, "gate/pay-penalty", require_auth=False)

# 4. Payment & Account
@app.get("/payment/transactions")
async def get_transactions(request: Request) -> Response:
    return await _proxy(request, PAYMENT_URL, "transactions", require_auth=True)

@app.get("/account/me") # Lưu ý URL ngắn gọn hơn
async def account_me(request: Request) -> Response:
    return await _proxy(request, ACCOUNT_URL, "internal/get/account/me", require_auth=True)

@app.post("/auth/login")
async def auth_login(request: Request) -> Response:
    return await _proxy(request, AUTH_URL, "post/authentication/login", require_auth=False)