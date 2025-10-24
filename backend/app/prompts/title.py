"""Prompt template for generating concise chat titles."""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate


def build_chat_title_prompt() -> ChatPromptTemplate:
    """Create a prompt that summarizes a conversation into a short title."""
    return ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                    "You are a helpful assistant that creates concise, professional titles for market analysis chats. "
                    "Return only the title text. Keep it under 60 characters, avoid quotation marks, and capitalize major words."
                )
            ),
            HumanMessage(
                content=(
                    "Conversation transcript:\n{history}\n\n"
                    "Provide a single title summarizing this conversation."
                )
            ),
        ]
    )


CHAT_TITLE_PROMPT = build_chat_title_prompt()
