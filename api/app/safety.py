"""Per-IP in-memory rate limiting and request safety middleware."""
from __future__ import annotations

import time
from collections import deque
from threading import Lock

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# 10 requests per minute with burst up to 15
_RATE_WINDOW_SECONDS = 60
_RATE_LIMIT_ASK = 10
_RATE_LIMIT_BURST = 15
_MAX_BODY_BYTES = 8_192  # 8 KB hard limit at app level

_lock = Lock()
# ip -> deque of timestamps
_ask_buckets: dict[str, deque] = {}


def reset_rate_limits() -> None:
    with _lock:
        _ask_buckets.clear()


def check_rate_limit(ip: str) -> None:
    now = time.monotonic()
    with _lock:
        if ip not in _ask_buckets:
            _ask_buckets[ip] = deque()
        bucket = _ask_buckets[ip]
        # Purge old entries
        while bucket and now - bucket[0] > _RATE_WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= _RATE_LIMIT_BURST:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please wait before asking again.",
            )
        bucket.append(now)


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "connect-src 'self';"
        )
        response.headers["X-Robots-Tag"] = "noindex"
        return response
