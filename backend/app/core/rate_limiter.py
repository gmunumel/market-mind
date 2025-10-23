from __future__ import annotations

import threading
from dataclasses import dataclass

from cachetools import TTLCache
from fastapi import HTTPException, status


@dataclass
class RateLimitResult:
    remaining_hourly: int
    remaining_daily: int


class RateLimiter:
    """In-memory request limiter keyed by user identifier."""

    def __init__(self, hourly_limit: int, daily_limit: int) -> None:
        self.hourly_limit = hourly_limit
        self.daily_limit = daily_limit
        self._hourly_cache: TTLCache[str, int] = TTLCache(maxsize=10000, ttl=3600)
        self._daily_cache: TTLCache[str, int] = TTLCache(maxsize=10000, ttl=86400)
        self._lock = threading.Lock()

    def check(self, user_id: str) -> RateLimitResult:
        """Increment counters and ensure limits are not exceeded."""
        with self._lock:
            hourly_count = self._hourly_cache.get(user_id, 0) + 1
            daily_count = self._daily_cache.get(user_id, 0) + 1

            if hourly_count > self.hourly_limit or daily_count > self.daily_limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please wait before sending more requests.",
                )

            self._hourly_cache[user_id] = hourly_count
            self._daily_cache[user_id] = daily_count

            return RateLimitResult(
                remaining_hourly=self.hourly_limit - hourly_count,
                remaining_daily=self.daily_limit - daily_count,
            )
