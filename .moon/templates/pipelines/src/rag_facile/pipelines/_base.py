"""Base interface for RAG pipeline orchestration.

Defines the :class:`RAGPipeline` ABC that concrete pipelines must implement.
Chat applications depend on this interface rather than on individual
ingestion or retrieval packages directly.
"""

from __future__ import annotations

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncGenerator
from uuid import uuid4


if TYPE_CHECKING:
    from albert import AsyncAlbertClient
    from rag_facile.core.schema import RetrievedChunk


logger = logging.getLogger(__name__)


class RAGPipeline(ABC):
    """Abstract RAG pipeline for chat applications.

    Provides a unified interface for upload-time (file processing),
    query-time (retrieval), and generation (LLM streaming + tracing).

    Subclasses must implement:
      - :meth:`process_file` — parse a file and return formatted context
      - :meth:`process_bytes` — parse bytes and return formatted context
      - :attr:`supported_extensions` — file extensions this pipeline handles
      - :attr:`accepted_mime_types` — MIME type map for file picker dialogs

    Optional overrides:
      - :meth:`retrieve_chunks` — return raw :class:`RetrievedChunk` list
        (default: empty list — used by :class:`~.basic.BasicPipeline`)
      - :meth:`process_query` — formatted context string
        (default: calls ``retrieve_chunks`` + ``format_context``)
    """

    # ── Upload-time: file processing ──

    @abstractmethod
    def process_file(
        self,
        path: str | Path,
        filename: str | None = None,
    ) -> str:
        """Parse a file and return formatted context for LLM injection.

        Args:
            path: Path to the document.
            filename: Optional display name.  Defaults to the file's basename.

        Returns:
            Formatted text ready for context injection.
        """

    @abstractmethod
    def process_bytes(self, data: bytes, filename: str) -> str:
        """Parse file bytes and return formatted context.

        Args:
            data: Raw file content.
            filename: Display name (also used to infer file type).

        Returns:
            Formatted text ready for context injection.
        """

    # ── Query-time: raw chunk retrieval ──

    def retrieve_chunks(self, query: str, **kwargs: object) -> list[RetrievedChunk]:
        """Retrieve raw chunks for a query.

        The default implementation returns an empty list — suitable for
        context-stuffing pipelines that pre-load the full document into
        the prompt.  The Albert pipeline overrides this to perform
        search → optional rerank.

        Args:
            query: User query to retrieve chunks for.
            **kwargs: Pipeline-specific options (e.g. ``collection_ids``).

        Returns:
            List of :class:`~rag_facile.core.schema.RetrievedChunk` dicts,
            sorted by relevance score (descending).  Empty list when not
            applicable.
        """
        return []

    # ── Query-time: formatted context string ──

    def process_query(self, query: str, **kwargs: object) -> str:
        """Retrieve relevant context for a user query as a formatted string.

        Calls :meth:`retrieve_chunks` then formats the result via
        :func:`~rag_facile.context.format_context`.  Override this method
        only if you need custom formatting logic.

        Args:
            query: User query to retrieve context for.
            **kwargs: Forwarded to :meth:`retrieve_chunks`.

        Returns:
            Formatted context string.  Empty string when no chunks found.
        """
        from rag_facile.context import format_context

        return format_context(self.retrieve_chunks(query, **kwargs))

    # ── Full RAG turn: retrieve + generate + trace ──

    async def stream_answer(
        self,
        question: str,
        message_history: list[dict[str, Any]],
        *,
        trace_id: str | None = None,
        session_id: str = "",
        **kwargs: object,
    ) -> AsyncGenerator[str, None]:
        """Full RAG turn: retrieve context, assemble prompt, stream LLM answer,
        and record a trace.

        This is the primary entry point for chat applications.  Apps call
        this method instead of managing the LLM client directly.

        Internally orchestrates:

        1. :meth:`retrieve_chunks` — pipeline-specific retrieval
        2. Prompt assembly — injects context into user message
        3. LLM streaming — yields tokens as they arrive
        4. Trace recording — writes to SQLite after the stream completes
           (only when ``tracing.enabled = true`` in config)

        Args:
            question: Current user question (raw, without context injection).
            message_history: Previous conversation turns, e.g.::

                [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user",      "content": "Bonjour"},
                    {"role": "assistant", "content": "Bonjour ! Comment puis-je vous aider ?"},
                ]

                Must **not** include the current turn.  This method appends
                it internally with context injected.

            trace_id: Optional pre-generated UUID4.  Auto-generated when
                *None*.  Pre-generating lets the caller associate user
                feedback with the trace before the stream completes.
            session_id: Identifier grouping multiple turns by conversation.
                Use the Chainlit session ID or Reflex ``client_token``.
            **kwargs: Forwarded to :meth:`retrieve_chunks` — e.g.
                ``collection_ids``.

        Yields:
            Token strings as they arrive from the LLM.

        Side effects:
            On completion, writes a :class:`~rag_facile.tracing.TraceRecord`
            to ``.rag-facile/traces.db`` when tracing is enabled.
        """
        from rag_facile.context import format_context
        from rag_facile.core import get_config

        config = get_config()
        t0 = time.monotonic()
        effective_trace_id = trace_id or str(uuid4())

        # Step 1 — Retrieval (subclass-specific)
        chunks = self.retrieve_chunks(question, **kwargs)

        # Step 2 — Prompt assembly
        retrieved_context = format_context(chunks)
        user_content = question
        if retrieved_context:
            user_content = (
                "Use the following context to answer the user's question:\n\n"
                f"{retrieved_context}\n\n"
                f"Question: {question}"
            )
        messages = [*message_history, {"role": "user", "content": user_content}]

        # Step 3 — LLM streaming
        model_alias = os.getenv("OPENAI_MODEL") or config.generation.model
        stream = await self._async_llm_client.chat.completions.create(  # ty: ignore[no-matching-overload]
            model=model_alias,
            messages=messages,
            stream=True,
            temperature=config.generation.temperature,
            max_tokens=config.generation.max_tokens,
        )

        resolved_model: str | None = None
        answer_tokens: list[str] = []

        try:
            async for chunk in stream:
                if resolved_model is None and getattr(chunk, "model", None):
                    resolved_model = chunk.model
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    answer_tokens.append(token)
                    yield token
        except json.JSONDecodeError:
            # Albert API occasionally sends malformed SSE events; continue
            # with whatever content was streamed so far.
            pass

        # Step 4 — Trace recording (after stream fully consumed)
        if config.tracing.enabled:
            system_prompt = next(
                (m["content"] for m in message_history if m.get("role") == "system"),
                None,
            )
            pipeline_config_snapshot = {
                "top_k": config.retrieval.top_k,
                "top_n": config.reranking.top_n,
                "retrieval_strategy": config.retrieval.strategy,
                "reranking_enabled": config.reranking.enabled,
                "temperature": config.generation.temperature,
                "query_strategy": config.query.strategy,
            }
            try:
                from rag_facile.tracing import get_store

                store = get_store(config)
                store.record_turn(
                    {
                        "trace_id": effective_trace_id,
                        "session_id": session_id,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "question": question,
                        "chunks": (
                            json.dumps(list(chunks))
                            if config.tracing.capture_chunks and chunks
                            else None
                        ),
                        "prompt_sent": (
                            user_content if config.tracing.capture_prompt else None
                        ),
                        "system_prompt": system_prompt,
                        "answer": "".join(answer_tokens),
                        "model_alias": model_alias,
                        "model_resolved": resolved_model,
                        "preset": config.meta.preset,
                        "pipeline_config": json.dumps(pipeline_config_snapshot),
                        "latency_ms": int((time.monotonic() - t0) * 1000),
                    }
                )
            except (OSError, RuntimeError) as exc:
                # Tracing must never break the chat experience
                logger.warning("Failed to record trace: %s", exc)

    # ── Async LLM client ──

    @property
    def _async_llm_client(self) -> AsyncAlbertClient:
        """Lazy async LLM client for generation, shared across all pipelines."""
        if not hasattr(self, "_async_llm_client_cache"):
            from albert import AsyncAlbertClient as _AsyncAlbertClient

            self._async_llm_client_cache = _AsyncAlbertClient(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
            )
        return self._async_llm_client_cache

    # ── Capabilities (for UI file dialogs) ──

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """File extensions this pipeline can process (e.g., ``[".pdf"]``)."""

    @property
    @abstractmethod
    def accepted_mime_types(self) -> dict[str, list[str]]:
        """MIME types for file picker dialogs.

        Returns:
            Dict mapping MIME types to extensions, e.g.
            ``{"application/pdf": [".pdf"]}``
        """
