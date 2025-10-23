from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration sourced from environment variables."""

    environment: Literal["development", "staging", "production", "test"] = "development"
    log_level: str = "INFO"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    frontend_origin: str = "http://localhost:5173"

    openai_api_key: str = "changeme"
    openai_model: str = "gpt-4o"

    database_url: str = "postgresql+psycopg://market_mind:market_mind@localhost:5432/market_mind"
    chroma_persist_directory: Path = Path("./data/chroma")

    duckduckgo_region: str = "wt-wt"

    langfuse_public_key: str = "changeme"
    langfuse_secret_key: str = "changeme"
    langfuse_host: str = "https://cloud.langfuse.com"

    hourly_request_limit: int = 60
    daily_request_limit: int = 500

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
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
    settings.chroma_persist_path.mkdir(parents=True, exist_ok=True)
    return settings
