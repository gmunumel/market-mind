from dataclasses import dataclass


@dataclass
class AgentResponse:
    """Represents the response of an agent to a user query."""
    answer: str
    search_results: list[str]
    vector_context: str
