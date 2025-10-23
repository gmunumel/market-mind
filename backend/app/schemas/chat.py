from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=8192)


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    metadata: dict[str, Any] | None = None

    class Config:
        from_attributes = True


class ChatSessionDetail(ChatSessionResponse):
    messages: list[MessageResponse] = []


class ChatResponse(BaseModel):
    message: MessageResponse
    ai_response: MessageResponse
