from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_rate_limiter
from app.core.config import get_settings
from app.core.rate_limiter import RateLimiter
from app.repositories import ChatRepository
from app.schemas import (
    ChatResponse,
    ChatSessionCreate,
    ChatSessionDetail,
    ChatSessionResponse,
    MessageCreate,
    MessageResponse,
)
from app.services import AgentService

router = APIRouter(prefix="/chats")

settings = get_settings()
agent_service = AgentService(settings=settings)


@router.get("", response_model=list[ChatSessionResponse])
def list_chats(db: Session = Depends(get_db)) -> list[ChatSessionResponse]:
    print("Listing chat sessions")
    repo = ChatRepository(db)
    return [ChatSessionResponse.model_validate(chat) for chat in repo.list_sessions()]


@router.post(
    "", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED
)
def create_chat(
    payload: ChatSessionCreate,
    db: Session = Depends(get_db),
) -> ChatSessionResponse:
    repo = ChatRepository(db)
    chat = repo.create_session(title=payload.title)
    return ChatSessionResponse.model_validate(chat)


@router.get("/{chat_id}", response_model=ChatSessionDetail)
def get_chat(chat_id: str, db: Session = Depends(get_db)) -> ChatSessionDetail:
    repo = ChatRepository(db)
    chat = repo.get_session(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found."
        )
    return ChatSessionDetail(
        **ChatSessionResponse.model_validate(chat).model_dump(),
        messages=[
            MessageResponse.model_validate(m) for m in repo.list_messages(chat_id)
        ],
    )


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(chat_id: str, db: Session = Depends(get_db)) -> Response:
    repo = ChatRepository(db)
    deleted = repo.delete_session(chat_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found."
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{chat_id}/title", response_model=ChatSessionResponse)
def refresh_chat_title(
    chat_id: str, db: Session = Depends(get_db)
) -> ChatSessionResponse:
    repo = ChatRepository(db)
    chat = repo.get_session(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found."
        )

    messages = repo.list_messages(chat_id)
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate a title without conversation history.",
        )

    recent_messages = list(messages)[-12:]
    history_text = "\n".join(f"{msg.role}: {msg.content}" for msg in recent_messages)
    title = agent_service.suggest_title(history_text)

    updated = repo.update_session_title(chat_id, title)
    if not updated:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update chat title.",
        )
    return ChatSessionResponse.model_validate(updated)


@router.post("/{chat_id}/messages", response_model=ChatResponse)
def post_message(
    chat_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    limiter: RateLimiter = Depends(get_rate_limiter),
    user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> ChatResponse:
    repo = ChatRepository(db)
    chat = repo.get_session(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found."
        )

    identifier = user_id or chat_id
    limiter.check(identifier)

    user_message = repo.add_message(
        chat_id=chat_id, role="user", content=payload.content
    )
    agent_service.persist_memory(chat_id, "user", payload.content)

    history_messages = repo.list_messages(chat_id)
    history_text = "\n".join(f"{msg.role}: {msg.content}" for msg in history_messages)

    agent_result = agent_service.generate_response(
        chat_id=chat_id,
        user_id=identifier,
        history=history_text,
        prompt=payload.content,
    )

    ai_message = repo.add_message(
        chat_id=chat_id,
        role="assistant",
        content=agent_result.answer,
        metadata={
            "search_results": agent_result.search_results,
            "vector_context": agent_result.vector_context,
        },
    )
    agent_service.persist_memory(chat_id, "assistant", agent_result.answer)

    return ChatResponse(
        message=MessageResponse.model_validate(user_message),
        ai_response=MessageResponse.model_validate(ai_message),
    )
