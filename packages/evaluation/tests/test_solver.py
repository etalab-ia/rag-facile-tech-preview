"""Tests for the inject_rag_context solver."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from rag_facile.evaluation._solvers import inject_rag_context


@pytest.mark.asyncio
async def test_inject_context_prepends() -> None:
    """Context is prepended to the user input."""
    solver = inject_rag_context()
    state = MagicMock()
    state.metadata = {
        "retrieved_contexts": ["Context A", "Context B"],
    }
    state.input_text = "What is RAG?"

    result = await solver(state, generate=None)

    assert "Context A" in result.input_text
    assert "Context B" in result.input_text
    assert "What is RAG?" in result.input_text
    assert result.input_text.index("Context A") < result.input_text.index(
        "What is RAG?"
    )


@pytest.mark.asyncio
async def test_inject_no_context() -> None:
    """When no contexts, input is unchanged."""
    solver = inject_rag_context()
    state = MagicMock()
    state.metadata = {"retrieved_contexts": []}
    state.input_text = "What is RAG?"

    result = await solver(state, generate=None)

    assert result.input_text == "What is RAG?"
