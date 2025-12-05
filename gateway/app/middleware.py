import json
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import redis.asyncio as redis

class IdempotencyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str):
        super().__init__(app)
        self.redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    async def dispatch(self, request: Request, call_next):
        if request.method != "POST":
            return await call_next(request)

        key = request.headers.get("Idempotency-Key")
        if not key:
            return await call_next(request)

        # Check cache
        cache_key = f"idempotency:{key}"
        cached_data = await self.redis.get(cache_key)
        
        if cached_data:
            data = json.loads(cached_data)
            return Response(
                content=data["body"],
                status_code=data["status_code"],
                headers=dict(data["headers"]),
                media_type=data["media_type"]
            )

        # Process request
        response = await call_next(request)

        # Cache success responses
        if 200 <= response.status_code < 300:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Reconstruct response for client
            client_response = Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

            # Save to redis
            await self.redis.setex(
                cache_key,
                60 * 60 * 24, # 24 hours
                json.dumps({
                    "body": body.decode("utf-8"),
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "media_type": response.media_type
                })
            )
            
            return client_response

        return response
