from fastapi import APIRouter

from app.api.routes import chats

api_router = APIRouter()
api_router.include_router(chats.router, tags=["chats"])

__all__ = ["api_router"]
