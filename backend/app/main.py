from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import get_settings
from app.core.logging import logger as app_logger
from app.db import Base, engine

logger = app_logger.getChild(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure DB tables exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")
    yield
    # Shutdown: add teardown logic here if needed


app = FastAPI(
    title="Market Mind Backend",
    version="0.1.0",
    description="LangGraph-powered AI agent for financial intelligence.",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://market-mind.stackedge.dev",
        "http://localhost",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router)
