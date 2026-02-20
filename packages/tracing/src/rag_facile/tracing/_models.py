"""TypedDicts for trace and feedback records."""

from __future__ import annotations

from typing import TypedDict


class TraceRecord(TypedDict):
    """A single RAG turn trace record stored in SQLite."""

    trace_id: str
    """UUID4 identifying this trace."""

    session_id: str
    """Chainlit/Reflex session token — groups turns by conversation."""

    created_at: str
    """ISO-8601 UTC timestamp, e.g. ``"2026-02-20T17:30:00.000000+00:00"``."""

    question: str
    """Raw user question before context injection."""

    chunks: str | None
    """JSON-serialised ``list[RetrievedChunk]`` or ``None`` when
    ``tracing.capture_chunks = false``."""

    prompt_sent: str | None
    """Full user message with injected context or ``None`` when
    ``tracing.capture_prompt = false``."""

    system_prompt: str | None
    """System prompt used for this turn."""

    answer: str
    """Complete LLM response (all streamed tokens joined)."""

    model_alias: str
    """Model alias sent to the API, e.g. ``"openweight-large"``."""

    model_resolved: str | None
    """Actual model ID from the API response, e.g.
    ``"meta-llama/Llama-3.3-70B-Instruct"``."""

    preset: str | None
    """Active preset name from ``config.meta.preset``."""

    pipeline_config: str
    """JSON snapshot of key pipeline parameters (top_k, top_n, strategy, …)."""

    latency_ms: int | None
    """End-to-end latency from question received to last token yielded."""


class FeedbackRecord(TypedDict):
    """User evaluation attached to a trace."""

    feedback_id: str
    """UUID4."""

    trace_id: str
    """FK → ``traces.trace_id``."""

    created_at: str
    """ISO-8601 UTC timestamp."""

    star_rating: int | None
    """1–5 star rating, or ``None`` if the user skipped rating."""

    sentiment: str | None
    """``"positive"`` | ``"negative"`` | ``None``."""

    tags: list[str]
    """Selected quality tags, e.g. ``["Pertinent", "Complet"]``."""

    comment: str | None
    """Free-text comment, or ``None``."""
