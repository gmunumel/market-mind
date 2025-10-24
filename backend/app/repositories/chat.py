from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChatSession, Message


class ChatRepository:
    """Data access layer for chat sessions and messages."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_session(self, title: str | None = None) -> ChatSession:
        chat = ChatSession(title=title or "Market Mind Chat")
        self.session.add(chat)
        self.session.commit()
        self.session.refresh(chat)
        return chat

    def list_sessions(self) -> Sequence[ChatSession]:
        stmt = select(ChatSession).order_by(ChatSession.updated_at.desc())
        return list(self.session.scalars(stmt))

    def get_session(self, chat_id: str) -> ChatSession | None:
        return self.session.get(ChatSession, chat_id)

    def delete_session(self, chat_id: str) -> bool:
        chat = self.get_session(chat_id)
        if not chat:
            return False
        self.session.delete(chat)
        self.session.commit()
        return True

    def update_session_title(self, chat_id: str, title: str) -> ChatSession | None:
        chat = self.get_session(chat_id)
        if not chat:
            return None
        chat.title = title
        self.session.add(chat)
        self.session.commit()
        self.session.refresh(chat)
        return chat

    def add_message(
        self,
        chat_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        message = Message(
            chat_session_id=chat_id,
            role=role,
            content=content,
            message_metadata=metadata,
        )
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        return message

    def list_messages(self, chat_id: str) -> Sequence[Message]:
        stmt = (
            select(Message)
            .where(Message.chat_session_id == chat_id)
            .order_by(Message.created_at.asc())
        )
        return list(self.session.scalars(stmt))
