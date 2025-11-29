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
BOOKING_URL = settings.BOOKING_SERVICE_URL.rstrip("/")
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

# Authentication
@app.post("/auth/authentication/login")
async def auth_login(request: Request) -> Response:
    return await _proxy(request, AUTH_URL, "post/authentication/login", require_auth=False)


@app.get("/account/accounts/me")
async def account_me(request: Request) -> Response:
    return await _proxy(request, ACCOUNT_URL, "internal/get/account/me", require_auth=True)


# Payment
@app.post("/payment/payments/init")
async def payment_init(request: Request) -> Response:
    return await _proxy(request, PAYMENT_URL, "post/payment/payment_init", require_auth=True)

@app.post("/payment/verify_otp")
async def payment_verify_otp(request: Request) -> Response:
    return await _proxy(request, PAYMENT_URL, "post/payment/verify_otp", require_auth=True)

@app.get("/payment/payments/history")
async def payment_history(request: Request) -> Response:
    return await _proxy(request, PAYMENT_URL, "get/payment/history", require_auth=True)

# Booking
@app.post("/booking/trip_confirm")
async def booking_confirm(request: Request) -> Response:
    return await _proxy(request, BOOKING_URL, "booking/post/trip_confirm", require_auth=True)

@app.get("/booking/booking/{booking_id}")
async def booking_get(booking_id: str, request: Request) -> Response:
    return await _proxy(request, BOOKING_URL, f"get/booking/{booking_id}", require_auth=True)

#Scheduler
@app.get("/route/trips")
async def route_trips(request: Request) -> Response:
    return await _proxy(request, SCHEDULER_URL, "get/route/trips", require_auth=True)