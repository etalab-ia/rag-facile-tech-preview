"""Tests for RAG evaluation solvers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rag_facile.evaluation._solvers import retrieve_rag_context


# ── Helpers ───────────────────────────────────────────────────────────────────

# Patch target: the module-level helper that calls the RAG pipeline.
# Tests patch this instead of the lazily-imported rag_facile.core / .pipelines
# modules (which aren't available in the evaluation package's test environment).
_PIPELINE_HELPER = "rag_facile.evaluation._solvers._call_pipeline"


def _make_state(question: str = "What is RAG?") -> MagicMock:
    """Create a mock TaskState."""
    from inspect_ai.model import ChatMessageUser

    state = MagicMock()
    state.input_text = question
    state.metadata = {}
    state.messages = [ChatMessageUser(content=question)]
    return state


# ── retrieve_rag_context ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_retrieve_injects_context() -> None:
    """When the pipeline returns context + chunk IDs, both are stored."""
    with patch(
        _PIPELINE_HELPER,
        return_value=(
            "RAG stands for Retrieval-Augmented Generation.",
            [1, 2, 3],
        ),
    ):
        solver = retrieve_rag_context()
        state = _make_state("What is RAG?")
        result = await solver(state, AsyncMock())

    # Context stored in metadata for faithfulness scorer
    assert "retrieved_contexts" in result.metadata
    assert len(result.metadata["retrieved_contexts"]) == 1
    assert "Retrieval-Augmented Generation" in result.metadata["retrieved_contexts"][0]

    # Chunk IDs stored for precision@k and recall@k
    assert "retrieved_chunk_ids" in result.metadata
    assert result.metadata["retrieved_chunk_ids"] == ["1", "2", "3"]

    # Context injected into the first message
    first_message = result.messages[0]
    assert "Retrieval-Augmented Generation" in first_message.content
    assert "What is RAG?" in first_message.content


@pytest.mark.asyncio
async def test_retrieve_no_context_passthrough() -> None:
    """When the pipeline returns no context, state is passed through unchanged."""
    with patch(_PIPELINE_HELPER, return_value=("", [])):
        solver = retrieve_rag_context()
        state = _make_state("What is RAG?")
        original_messages = state.messages[:]
        result = await solver(state, AsyncMock())

    # State unchanged
    assert result is state
    assert result.messages == original_messages
    assert "retrieved_contexts" not in result.metadata


@pytest.mark.asyncio
async def test_retrieve_pipeline_failure_passthrough() -> None:
    """When the pipeline raises, state is passed through unchanged (non-fatal)."""
    with patch(_PIPELINE_HELPER, side_effect=RuntimeError("pipeline unavailable")):
        solver = retrieve_rag_context()
        state = _make_state("What is RAG?")
        result = await solver(state, AsyncMock())

    assert result is state
    assert "retrieved_contexts" not in result.metadata
