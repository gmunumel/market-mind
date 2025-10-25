from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.rate_limiter import RateLimiter
from app.db import SessionLocal

settings = get_settings()
rate_limiter = RateLimiter(
    hourly_limit=settings.hourly_request_limit,
    daily_limit=settings.daily_request_limit,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_rate_limiter() -> RateLimiter:
    return rate_limiter
