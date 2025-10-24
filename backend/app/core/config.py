import logging
import socket
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

_ROOT_DIR = Path(__file__).resolve().parents[3]
_env_files = (str(_ROOT_DIR / ".env"), str(_ROOT_DIR / ".env.local"))


class Settings(BaseSettings):
    """Application configuration sourced from environment variables."""

    environment: Literal["development", "staging",
                         "production", "test"] = "development"
    log_level: str = "INFO"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    frontend_origin: str = "http://localhost:5173"

    openai_api_key: str = "changeme"
    openai_model: str = "gpt-4o"

    _default_db_path: Path = _ROOT_DIR / "data" / "market_mind.db"
    database_url: str = f"sqlite:///{_default_db_path.as_posix()}"
    chroma_persist_directory: Path = _ROOT_DIR / "data" / "chroma"

    duckduckgo_region: str = "wt-wt"

    langfuse_public_key: str = "changeme"
    langfuse_secret_key: str = "changeme"
    langfuse_host: str = "https://cloud.langfuse.com"

    hourly_request_limit: int = 60
    daily_request_limit: int = 500

    model_config = SettingsConfigDict(
        env_file=_env_files,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def chroma_persist_path(self) -> Path:
        return Path(self.chroma_persist_directory).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    settings = Settings()
    logger = logging.getLogger(__name__)

    # ensure chroma dir exists, but fall back to project-local path if permissions prevent creation
    try:
        settings.chroma_persist_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        fallback_path = (_ROOT_DIR / "data" / "chroma").resolve()
        fallback_path.mkdir(parents=True, exist_ok=True)
        settings.chroma_persist_directory = fallback_path

    # If configured for Postgres but hostname is unavailable (common in local dev), fall back to SQLite.
    try:
        db_url = make_url(settings.database_url)
    except ArgumentError:
        db_url = None
    if (
        db_url
        and db_url.get_backend_name().startswith("postgresql")
        and settings.environment != "production"
        and db_url.host
    ):
        try:
            socket.getaddrinfo(db_url.host, db_url.port or 0)
        except OSError:
            fallback_db_path = settings._default_db_path.resolve()
            fallback_db_path.parent.mkdir(parents=True, exist_ok=True)
            settings.database_url = f"sqlite:///{fallback_db_path.as_posix()}"
            logger.warning(
                "Database host '%s' unavailable; falling back to local SQLite database at %s.",
                db_url.host,
                fallback_db_path,
            )

    # normalize sqlite URL to use a POSIX path (sqlite URIs expect forward slashes)
    if settings.database_url.startswith("sqlite:///") and ":memory:" not in settings.database_url:
        db_path = Path(settings.database_url.replace(
            "sqlite:///", "", 1)).resolve()
        # ensure parent dir exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # rewrite database_url to a normalized form (use as_posix() so URI works on Windows)
        settings.database_url = f"sqlite:///{db_path.as_posix()}"
    return settings
