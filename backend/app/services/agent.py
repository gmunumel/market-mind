from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict

from duckduckgo_search import DDGS
from langchain.docstore.document import Document
from langchain.prompts import ChatPromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.vectorstores import Chroma
from langfuse import Langfuse
from langgraph.graph import END, StateGraph

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
except ImportError:  # pragma: no cover - handled in tests if optional dep missing
    ChatOpenAI = None  # type: ignore
    OpenAIEmbeddings = None  # type: ignore

logger = get_logger(__name__)


class AgentState(TypedDict, total=False):
    question: str
    history: str
    search_results: list[str]
    vector_context: str
    answer: str


class SimpleChatModel:
    """Fallback LLM used when OpenAI credentials are unavailable."""

    def invoke(self, messages: list[Any], **_: Any) -> AIMessage:
        user_message = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), "")
        content = (
            "This is a placeholder response because no OpenAI API key is configured. "
            f"You asked: {user_message}"
        )
        return AIMessage(content=content)


class FakeEmbeddings:
    """Deterministic embedding fallback."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float((sum(map(ord, text)) % 100) / 10.0) for _ in range(1536)]


@dataclass
class AgentResponse:
    answer: str
    search_results: list[str]
    vector_context: str


class AgentService:
    """Orchestrates the LangGraph workflow for Market Mind responses."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.llm = self._build_llm()
        self.embeddings = self._build_embeddings()
        self.vector_store = Chroma(
            collection_name="market-mind",
            persist_directory=str(self.settings.chroma_persist_path),
            embedding_function=self.embeddings,
        )
        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=(
                        "You are Market Mind, an AI financial research analyst. "
                        "Your goals:\n"
                        "1. Fetch and summarize real-time financial or crypto data.\n"
                        "2. Generate insights or predictions highlighting market sentiment.\n"
                        "3. Provide actionable investment guidance based on real-time context.\n"
                        "Be transparent about data freshness and uncertainty. "
                        "Make clear if information is missing."
                    )
                ),
                HumanMessage(
                    content=(
                        "Conversation so far:\n{history}\n\n"
                        "Relevant knowledge base context:\n{vector_context}\n\n"
                        "Latest market signals:\n{search_results}\n\n"
                        "User request: {question}"
                    )
                ),
            ]
        )
        self.graph = self._build_graph()
        self.langfuse = self._build_langfuse()

    def _build_llm(self) -> Any:
        if ChatOpenAI and self.settings.openai_api_key not in {"", "changeme"}:
            return ChatOpenAI(
                model=self.settings.openai_model,
                temperature=0.2,
                openai_api_key=self.settings.openai_api_key,
            )
        logger.warning("Using SimpleChatModel fallback; configure OPENAI_API_KEY for real responses.")
        return SimpleChatModel()

    def _build_embeddings(self) -> Any:
        if OpenAIEmbeddings and self.settings.openai_api_key not in {"", "changeme"}:
            return OpenAIEmbeddings(openai_api_key=self.settings.openai_api_key, model="text-embedding-3-small")
        return FakeEmbeddings()

    def _build_langfuse(self) -> Langfuse | None:
        if self.settings.langfuse_public_key in {"", "changeme"} or self.settings.langfuse_secret_key in {
            "",
            "changeme",
        }:
            logger.info("Langfuse disabled; configure credentials to enable tracing.")
            return None
        return Langfuse(
            public_key=self.settings.langfuse_public_key,
            secret_key=self.settings.langfuse_secret_key,
            host=self.settings.langfuse_host,
        )

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("search_market", self._search_market)
        graph.add_node("retrieve_memory", self._retrieve_memory)
        graph.add_node("compose_answer", self._compose_answer)
        graph.set_entry_point("search_market")
        graph.add_edge("search_market", "retrieve_memory")
        graph.add_edge("retrieve_memory", "compose_answer")
        graph.add_edge("compose_answer", END)
        return graph.compile()

    def _search_market(self, state: AgentState) -> AgentState:
        if self.settings.environment == "test":
            state["search_results"] = ["Test mode: market data unavailable."]
            return state

        query = state.get("question") or ""
        results: list[str] = []
        try:
            with DDGS() as search:
                for item in search.news(query, max_results=3):
                    title = item.get("title")
                    snippet = item.get("body")
                    source = item.get("source")
                    if title or snippet:
                        results.append(f"{title} - {snippet} (source: {source})")
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("DuckDuckGo search failed: %s", exc)
            results.append("Live market search unavailable; proceeding with existing knowledge.")

        state["search_results"] = results
        return state

    def _retrieve_memory(self, state: AgentState) -> AgentState:
        question = state.get("question") or ""
        docs: list[Document] = []
        if question:
            try:
                docs = self.vector_store.similarity_search(question, k=4)
            except Exception as exc:  # pragma: no cover - chroma edge case
                logger.warning("Vector store retrieval failed: %s", exc)
        state["vector_context"] = "\n---\n".join(doc.page_content for doc in docs) if docs else "None"
        return state

    def _compose_answer(self, state: AgentState) -> AgentState:
        chain = self.prompt | self.llm
        rendered = chain.invoke(
            {
                "history": state.get("history", "None"),
                "vector_context": state.get("vector_context", "None"),
                "search_results": "\n".join(state.get("search_results", [])) or "No live data found.",
                "question": state.get("question", ""),
            }
        )
        if isinstance(rendered, AIMessage):
            state["answer"] = rendered.content
        else:  # pragma: no cover - depends on LLM interface
            state["answer"] = str(rendered)
        return state

    def persist_memory(self, chat_id: str, role: str, content: str) -> None:
        """Index messages into the vector store for long-term recall."""
        metadata = {"chat_id": chat_id, "role": role}
        try:
            self.vector_store.add_texts([content], metadatas=[metadata])
        except Exception as exc:  # pragma: no cover - external dependency
            logger.warning("Failed to persist memory: %s", exc)

    def generate_response(self, *, chat_id: str, user_id: str, history: str, prompt: str) -> AgentResponse:
        trace = None
        if self.langfuse:
            trace = self.langfuse.trace(
                name="market-mind-chat",
                user_id=user_id,
                input=prompt,
                metadata={"chat_id": chat_id},
            )

        try:
            state = self.graph.invoke({"question": prompt, "history": history})
            answer = state.get("answer", "I was unable to generate an answer.")
            search_summary = state.get("search_results", [])
            vector_context = state.get("vector_context", "")

            if trace:
                trace.update(output=answer)
                trace.end()
        except Exception as exc:
            logger.exception("Agent generation failed: %s", exc)
            if trace:
                trace.update(error=str(exc))
                trace.end()
            answer = "I encountered an internal error while generating a response."
            search_summary = ["Agent pipeline failed"]
            vector_context = "None"

        return AgentResponse(answer=answer, search_results=search_summary, vector_context=vector_context)
