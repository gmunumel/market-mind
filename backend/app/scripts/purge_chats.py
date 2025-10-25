from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from typing import Tuple

from sqlalchemy import delete

from app.db import session_scope
from app.models import ChatSession, Message


def purge_chats(older_than_hours: int | None = None) -> Tuple[int, int]:
    """Delete chats (and their messages) older than the provided cutoff."""
    cutoff = None
    if older_than_hours is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)

    with session_scope() as session:
        msg_stmt = delete(Message)
        chat_stmt = delete(ChatSession)

        if cutoff is not None:
            msg_stmt = msg_stmt.where(Message.created_at < cutoff)
            chat_stmt = chat_stmt.where(ChatSession.updated_at < cutoff)

        msg_result = session.execute(msg_stmt)
        chat_result = session.execute(chat_stmt)

        deleted_messages = msg_result.rowcount or 0
        deleted_chats = chat_result.rowcount or 0

        return deleted_messages, deleted_chats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Purge chat history from the Market Mind database."
    )
    parser.add_argument(
        "--older-than-hours",
        type=int,
        default=None,
        help="Only delete chats older than this many hours. Omit to delete everything.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    deleted_messages, deleted_chats = purge_chats(args.older_than_hours)
    scope = (
        f"older than {args.older_than_hours}h" if args.older_than_hours is not None else "all chats"
    )
    print(
        f"Purged {deleted_chats} chats and {deleted_messages} messages ({scope}).",
        flush=True,
    )


if __name__ == "__main__":
    main()
