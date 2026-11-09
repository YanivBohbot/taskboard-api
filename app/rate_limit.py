"""In-process ASGI rate limiting middleware."""

from collections.abc import Callable
from math import ceil
from threading import Lock

from starlette.types import ASGIApp, Receive, Scope, Send

from app.errors import problem

DEFAULT_RATE_LIMIT = 60
WINDOW_SECONDS = 60
HEALTH_PATH = "/health"
UNKNOWN_CLIENT = "unknown"
TOO_MANY_REQUESTS = 429


class FixedWindowRateLimiter:
    def __init__(
        self,
        limit: int = DEFAULT_RATE_LIMIT,
        window_seconds: int = WINDOW_SECONDS,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._clock = clock
        self._windows: dict[str, tuple[float, int]] = {}
        self._lock = Lock()

    def allow(self, client_ip: str) -> tuple[bool, int]:
        now = self._now()
        with self._lock:
            window_start, count = self._windows.get(client_ip, (now, 0))
            if now - window_start >= self.window_seconds:
                window_start = now
                count = 0

            if count >= self.limit:
                retry_after = max(0, ceil(self.window_seconds - (now - window_start)))
                return False, retry_after

            self._windows[client_ip] = (window_start, count + 1)
            return True, 0

    def reset(self) -> None:
        with self._lock:
            self._windows.clear()

    def _now(self) -> float:
        if self._clock is not None:
            return self._clock()

        import time

        return time.monotonic()


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp, limiter: FixedWindowRateLimiter) -> None:
        self.app = app
        self.limiter = limiter

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or self._is_exempt(scope):
            await self.app(scope, receive, send)
            return

        client_ip = self._client_ip(scope)
        allowed, retry_after = self.limiter.allow(client_ip)
        if allowed:
            await self.app(scope, receive, send)
            return

        response = problem(
            TOO_MANY_REQUESTS,
            "Too Many Requests",
            "Rate limit exceeded. Retry after the number of seconds in the Retry-After header.",
        )
        response.headers["Retry-After"] = str(retry_after)
        await response(scope, receive, send)

    def _is_exempt(self, scope: Scope) -> bool:
        return scope.get("method") == "GET" and scope.get("path") == HEALTH_PATH

    def _client_ip(self, scope: Scope) -> str:
        client = scope.get("client")
        if isinstance(client, tuple) and client:
            return str(client[0])
        return UNKNOWN_CLIENT
