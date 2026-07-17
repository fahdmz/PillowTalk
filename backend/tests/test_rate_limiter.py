from datetime import datetime, timedelta, timezone

import pytest

from app.services.rate_limiter import InMemoryRateLimiter, RateLimitExceeded


def test_rate_limiter_rejects_requests_past_user_window_limit():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)
    now = datetime(2026, 7, 17, tzinfo=timezone.utc)

    limiter.check("user-1", now=now)
    limiter.check("user-1", now=now + timedelta(seconds=1))

    with pytest.raises(RateLimitExceeded) as raised:
        limiter.check("user-1", now=now + timedelta(seconds=2))
    assert 0 < raised.value.retry_after_seconds <= 60


def test_rate_limit_is_independent_per_user_and_resets_after_window():
    limiter = InMemoryRateLimiter(max_requests=1, window_seconds=10)
    now = datetime(2026, 7, 17, tzinfo=timezone.utc)

    limiter.check("user-1", now=now)
    limiter.check("user-2", now=now)
    limiter.check("user-1", now=now + timedelta(seconds=11))
