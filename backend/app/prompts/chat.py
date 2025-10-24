"""Prompt templates for chat interactions with Market Mind."""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

MARKET_MIND_SYSTEM_MESSAGE = SystemMessage(
    content=(
        "You are Market Mind, an AI financial research analyst. "
        "Your goals:\n"
        "1. Fetch and summarize real-time financial or crypto data.\n"
        "2. Generate insights or predictions highlighting market sentiment.\n"
        "3. Provide actionable investment guidance based on real-time context.\n"
        "Be transparent about data freshness and uncertainty. "
        "Make clear if information is missing."
    )
)

MARKET_MIND_HUMAN_MESSAGE = HumanMessage(
    content=(
        "Conversation so far:\n{history}\n\n"
        "Relevant knowledge base context:\n{vector_context}\n\n"
        "Latest market signals:\n{search_results}\n\n"
        "User request: {question}"
    )
)


def build_market_mind_prompt() -> ChatPromptTemplate:
    """Constructs the default Market Mind chat prompt."""
    return ChatPromptTemplate.from_messages(
        [
            MARKET_MIND_SYSTEM_MESSAGE,
            MARKET_MIND_HUMAN_MESSAGE,
        ]
    )


MARKET_MIND_PROMPT = build_market_mind_prompt()
