from __future__ import annotations

import json
from typing import Any

from langchain_chroma import Chroma as ChromaVectorStore
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langfuse.langchain import CallbackHandler
from langgraph.graph import END, StateGraph
from pydantic import SecretStr

from app.core.config import Settings, get_settings
from app.core.logging import logger as app_logger
from app.models.agent_response import AgentResponse
from app.models.agent_state import AgentState
from app.prompts import build_market_mind_prompt, build_chat_title_prompt

logger = app_logger.getChild(__name__)
langfuse_callback = CallbackHandler()


class AgentService:
    """Orchestrates the LangGraph workflow for Market Mind responses."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.llm = self._build_llm()
        self.embeddings = self._build_embeddings()
        self.vector_store = self._build_vector_store()
        self.prompt = build_market_mind_prompt()
        self.title_prompt = build_chat_title_prompt()
        self.graph = self._build_graph()

    def _build_llm(self) -> Any:
        if self.settings.openai_api_key not in {"", "changeme"}:
            logger.info("Using ChatOpenAI for language model.")
            return ChatOpenAI(
                model=self.settings.openai_model,
                temperature=0.2,
                api_key=SecretStr(self.settings.openai_api_key),
            )
        logger.warning("Configure OPENAI_API_KEY for real responses.")
        raise RuntimeError("OpenAI API key not configured.")

    def _build_embeddings(self) -> Any:
        if self.settings.openai_api_key not in {"", "changeme"}:
            logger.info("Using OpenAIEmbeddings for vector memory.")
            return OpenAIEmbeddings(
                api_key=SecretStr(self.settings.openai_api_key),
                model="text-embedding-3-small",
            )
        logger.warning("Configure OPENAI_API_KEY for vector memory")
        raise RuntimeError("OpenAI API key not configured.")

    def _build_vector_store(self) -> Any | None:
        try:
            return ChromaVectorStore(
                collection_name="market-mind",
                embedding_function=self.embeddings,
                persist_directory=str(self.settings.chroma_persist_path),
            )
        except RuntimeError as exc:
            logger.warning("Chroma unavailable; disabling vector memory: %s", exc)
        return None

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
        raw = ""
        try:
            search = DuckDuckGoSearchResults()
            raw = search.run(query, max_results=3)

            try:
                items = json.loads(raw)
                for item in items:
                    title = item.get("title")
                    snippet = item.get("body")
                    source = item.get("source")
                    if title or snippet:
                        results.append(f"{title} - {snippet} (source: {source})")
            except (json.JSONDecodeError, ValueError):
                # Fallback when the search tool returns plain text or HTML instead of JSON.
                text = (raw or "").strip()
                if text:
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    # Keep a few concise lines as results
                    for line in lines[:3]:
                        results.append(
                            line if len(line) <= 1000 else line[:1000] + "..."
                        )
                else:
                    results.append("Live market search returned no parsable results.")
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("DuckDuckGo search failed: %s", exc)
            if raw:
                # Include a short excerpt of raw output to aid debugging but avoid huge payloads.
                results.append(f"Live market search returned raw output: {raw[:1000]}")
            else:
                results.append(
                    "Live market search unavailable; proceeding with existing knowledge."
                )

        state["search_results"] = results
        return state

    def _retrieve_memory(self, state: AgentState) -> AgentState:
        question = state.get("question") or ""
        docs: list[Document] = []
        if question and self.vector_store:
            try:
                docs = self.vector_store.similarity_search(question, k=4)
            except Exception as exc:  # pragma: no cover - chroma edge case
                logger.warning("Vector store retrieval failed: %s", exc)
        state["vector_context"] = (
            "\n---\n".join(doc.page_content for doc in docs) if docs else "None"
        )
        return state

    def _compose_answer(self, state: AgentState) -> AgentState:
        chain = self.prompt | self.llm
        rendered = chain.invoke(
            {
                "history": state.get("history", "None"),
                "vector_context": state.get("vector_context", "None"),
                "search_results": "\n".join(state.get("search_results", []))
                or "No live data found.",
                "question": state.get("question", ""),
            },
            config={"callbacks": [langfuse_callback]},
        )
        if isinstance(rendered, AIMessage):
            state["answer"] = str(rendered.content)
        else:  # pragma: no cover - depends on LLM interface
            state["answer"] = str(rendered)
        return state

    def persist_memory(self, chat_id: str, role: str, content: str) -> None:
        """Index messages into the vector store for long-term recall."""
        if not self.vector_store:
            return
        metadata = {"chat_id": chat_id, "role": role}
        try:
            self.vector_store.add_texts([content], metadatas=[metadata])
        except Exception as exc:  # pragma: no cover - external dependency
            logger.warning("Failed to persist memory: %s", exc)

    def generate_response(
        self, *, chat_id: str, user_id: str, history: str, prompt: str
    ) -> AgentResponse:
        """Generates an agent response given the user prompt and chat history."""
        try:
            state = self.graph.invoke(
                {"question": prompt, "history": history},
                config={"callbacks": [langfuse_callback]},
            )
            answer = state.get("answer", "I was unable to generate an answer.")
            search_summary = state.get("search_results", [])
            vector_context = state.get("vector_context", "")

        except Exception as exc:
            logger.exception("Agent generation failed: %s", exc)

            answer = "I encountered an internal error while generating a response."
            search_summary = ["Agent pipeline failed"]
            vector_context = "None"

        return AgentResponse(
            answer=answer, search_results=search_summary, vector_context=vector_context
        )

    def suggest_title(self, history: str) -> str:
        """Generate a concise chat title from the conversation history."""
        history = history.strip()
        if not history:
            return "Market Mind Chat"

        try:
            chain = self.title_prompt | self.llm
            rendered = chain.invoke(
                {"history": history}, config={"callbacks": [langfuse_callback]}
            )
            if isinstance(rendered, AIMessage):
                title = str(rendered.content).strip()
            else:  # pragma: no cover - depends on LLM interface
                title = str(rendered).strip()
        except Exception as exc:  # pragma: no cover - LLM or tool failure
            logger.warning("Failed to generate chat title: %s", exc)
            title = ""

        cleaned = (title.splitlines()[0] if title else "").strip()
        if not cleaned:
            preview = history.splitlines()[0] if history else "Market Mind Chat"
            cleaned = preview[:60].rstrip()
        return cleaned or "Market Mind Chat"
