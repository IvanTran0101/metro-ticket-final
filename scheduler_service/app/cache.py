from __future__ import annotations
import json
import redis
from functools import lru_cache
from typing import Any, Optional
from scheduler_service.app.settings import settings

@lru_cache()
def _redis() -> redis.Redis:
    return redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )

def get_cache(key: str) -> Optional[Any]:
    try:
        data = _redis().get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        print(f"Redis get error: {e}")
    return None

def set_cache(key: str, value: Any, ttl: int = 3600):
    try:
        _redis().setex(key, ttl, json.dumps(value))
    except Exception as e:
        print(f"Redis set error: {e}")
