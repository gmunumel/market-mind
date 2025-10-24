from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import get_settings
from app.core.logging import logger as app_logger
from app.db import Base, engine

logger = app_logger.getChild(__name__)
settings = get_settings()

app = FastAPI(
    title="Market Mind Backend",
    version="0.1.0",
    description="LangGraph-powered AI agent for financial intelligence.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")


app.include_router(api_router)
