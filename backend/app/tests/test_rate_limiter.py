import pytest
from fastapi import HTTPException

from app.core.rate_limiter import RateLimiter


def test_rate_limiter_allows_within_limits():
    limiter = RateLimiter(hourly_limit=2, daily_limit=5)

    result = limiter.check("user-1")
    assert result.remaining_hourly == 1
    assert result.remaining_daily == 4

    result = limiter.check("user-1")
    assert result.remaining_hourly == 0
    assert result.remaining_daily == 3


def test_rate_limiter_blocks_when_limit_exceeded():
    limiter = RateLimiter(hourly_limit=1, daily_limit=1)
    limiter.check("user-2")

    with pytest.raises(HTTPException) as exc_info:
        limiter.check("user-2")

    assert exc_info.value.status_code == 429
