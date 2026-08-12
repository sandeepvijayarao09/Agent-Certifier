"""Security utilities: rate limiting, security headers, input sanitization."""
import re
import time
import threading
from collections import defaultdict, deque

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Filenames may only keep word chars, dots, dashes and spaces after basename extraction
_FILENAME_SAFE = re.compile(r"[^\w.\- ]")
MAX_FILENAME_LENGTH = 128


def sanitize_filename(filename: str) -> str:
    """Strip path components and unsafe characters from an uploaded filename."""
    # Take the last path segment for both POSIX and Windows separators
    name = filename.replace("\\", "/").rsplit("/", 1)[-1]
    name = name.replace("\x00", "")
    name = _FILENAME_SAFE.sub("_", name).strip(". ")
    if not name:
        name = "unnamed"
    if len(name) > MAX_FILENAME_LENGTH:
        stem, dot, ext = name.rpartition(".")
        if dot and len(ext) <= 12:
            name = stem[: MAX_FILENAME_LENGTH - len(ext) - 1] + "." + ext
        else:
            name = name[:MAX_FILENAME_LENGTH]
    return name


class SlidingWindowRateLimiter:
    """In-memory per-client sliding window rate limiter.

    Suitable for a single-process deployment; swap for a shared store
    (e.g. Redis) when running multiple workers.
    """

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] < cutoff:
                hits.popleft()
            if len(hits) >= self.max_requests:
                return False
            hits.append(now)
            # Opportunistic cleanup so idle clients don't accumulate forever
            if len(self._hits) > 10_000:
                for k in [k for k, v in self._hits.items() if not v or v[-1] < cutoff]:
                    del self._hits[k]
            return True


def client_ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"


def enforce_rate_limit(limiter: SlidingWindowRateLimiter, request: Request) -> None:
    if not limiter.check(client_ip(request)):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please slow down and try again shortly.",
        )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        # Swagger UI (/docs, /redoc) needs scripts/styles; lock down everything else
        if not request.url.path.startswith(("/docs", "/redoc")):
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'none'; frame-ancestors 'none'",
            )
        return response
