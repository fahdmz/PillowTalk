"""Small per-process authenticated-user rate limiter for the API tier."""

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from threading import Lock

from fastapi import HTTPException


class RateLimitExceeded(HTTPException):
    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = max(1, retry_after_seconds)
        super().__init__(
            status_code=429,
            detail="Chat rate limit exceeded",
            headers={"Retry-After": str(self.retry_after_seconds)},
        )


class InMemoryRateLimiter:
    def __init__(self, *, max_requests: int, window_seconds: int) -> None:
        if max_requests <= 0 or window_seconds <= 0:
            raise ValueError("Rate limit values must be positive")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[datetime]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, user_id: str, *, now: datetime | None = None) -> None:
        current_time = now or datetime.now(timezone.utc)
        cutoff = current_time - timedelta(seconds=self.window_seconds)
        with self._lock:
            requests = self._requests[user_id]
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if len(requests) >= self.max_requests:
                retry_at = requests[0] + timedelta(seconds=self.window_seconds)
                retry_seconds = int((retry_at - current_time).total_seconds()) + 1
                raise RateLimitExceeded(retry_seconds)
            requests.append(current_time)
