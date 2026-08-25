"""
Lightweight in-memory sliding-window rate limiter, keyed by client IP.

This is intentionally simple (no external dependency like Redis) so the
MVP runs standalone. It's isolated behind this module so it can be
swapped for a Redis-backed limiter later (e.g. when scaling beyond a
single backend process) without touching the API routes.
"""
import time
from collections import defaultdict, deque
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

_request_log: dict[str, deque] = defaultdict(deque)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60.0
        log = _request_log[client_ip]

        while log and now - log[0] > window:
            log.popleft()

        if len(log) >= settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again in a moment."},
            )

        log.append(now)
        return await call_next(request)
