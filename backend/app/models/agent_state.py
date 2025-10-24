from typing import TypedDict


class AgentState(TypedDict, total=False):
    """Represents the state of an agent during a session."""
    question: str
    history: str
    search_results: list[str]
    vector_context: str
    answer: str
