"""Tests for RAG evaluation scorers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rag_facile.evaluation._scorers import (
    _parse_faithfulness_score,
    _parse_score,
    answer_correctness,
    faithfulness,
    precision_at_k,
    recall_at_k,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_state(
    *,
    retrieved_chunk_ids: list[str] | None = None,
    relevant_chunk_ids: list[str] | None = None,
    retrieved_contexts: list[str] | None = None,
    completion: str = "test answer",
    input_text: str = "test question",
) -> MagicMock:
    """Create a mock TaskState with metadata."""
    state = MagicMock()
    state.metadata = {
        "retrieved_chunk_ids": retrieved_chunk_ids or [],
        "relevant_chunk_ids": relevant_chunk_ids or [],
        "retrieved_contexts": retrieved_contexts or [],
    }
    state.output = MagicMock()
    state.output.completion = completion
    state.input_text = input_text
    return state


def _make_target(text: str = "reference answer") -> MagicMock:
    target = MagicMock()
    target.target = text
    return target


# ── score parser ──────────────────────────────────────────────────────────────


def test_parse_score_valid() -> None:
    assert _parse_score("SCORE: 0.85") == 0.85


def test_parse_score_lowercase() -> None:
    assert _parse_score("score: 0.5") == 0.5


def test_parse_score_clamped() -> None:
    assert _parse_score("SCORE: 1.5") == 1.0
    assert _parse_score("SCORE: -0.3") == 0.0


def test_parse_score_missing() -> None:
    assert _parse_score("no score here") == 0.0


def test_parse_faithfulness_score_alias() -> None:
    """Backwards-compat alias still works."""
    assert _parse_faithfulness_score("SCORE: 0.75") == 0.75


# ── faithfulness ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_faithfulness_no_answer() -> None:
    scorer = faithfulness(model="test")
    state = _make_state(retrieved_contexts=["some context"], completion="")
    result = await scorer(state, _make_target())
    assert result.value == 0.0


@pytest.mark.asyncio
async def test_faithfulness_no_context() -> None:
    """No context → vacuously true (we can't judge faithfulness without context)."""
    scorer = faithfulness(model="test")
    state = _make_state(retrieved_contexts=[], completion="some answer")
    result = await scorer(state, _make_target())
    assert result.value == 1.0


@pytest.mark.asyncio
async def test_faithfulness_calls_grader() -> None:
    """Faithfulness scorer calls the grader model and parses SCORE."""
    mock_model = MagicMock()
    mock_result = MagicMock()
    mock_result.completion = "- Claim A: SUPPORTED\nSCORE: 0.9"
    mock_model.generate = AsyncMock(return_value=mock_result)

    with patch("rag_facile.evaluation._scorers.get_model", return_value=mock_model):
        scorer = faithfulness(model="test")
        state = _make_state(
            retrieved_contexts=["Paris is the capital of France."],
            completion="France's capital is Paris.",
        )
        result = await scorer(state, _make_target())

    assert result.value == 0.9


# ── answer_correctness ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_answer_correctness_no_answer() -> None:
    scorer = answer_correctness(model="test")
    state = _make_state(completion="")
    result = await scorer(state, _make_target("reference"))
    assert result.value == 0.0


@pytest.mark.asyncio
async def test_answer_correctness_no_reference() -> None:
    """No reference → vacuously true."""
    scorer = answer_correctness(model="test")
    state = _make_state(completion="some answer")
    result = await scorer(state, _make_target(""))
    assert result.value == 1.0


@pytest.mark.asyncio
async def test_answer_correctness_calls_grader() -> None:
    """answer_correctness calls the grader model and parses SCORE."""
    mock_model = MagicMock()
    mock_result = MagicMock()
    mock_result.completion = "- Fact 1: COVERS\n- Fact 2: COVERS\nSCORE: 1.0"
    mock_model.generate = AsyncMock(return_value=mock_result)

    with patch("rag_facile.evaluation._scorers.get_model", return_value=mock_model):
        scorer = answer_correctness(model="test")
        state = _make_state(completion="The capital of France is Paris.")
        result = await scorer(state, _make_target("Paris is the capital of France."))

    assert result.value == 1.0


# ── recall_at_k (legacy) ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_recall_perfect() -> None:
    scorer = recall_at_k()
    state = _make_state(
        relevant_chunk_ids=["a", "b"],
        retrieved_chunk_ids=["a", "b", "c"],
    )
    result = await scorer(state, _make_target())
    assert result.value == 1.0


@pytest.mark.asyncio
async def test_recall_partial() -> None:
    scorer = recall_at_k()
    state = _make_state(
        relevant_chunk_ids=["a", "b", "c", "d"],
        retrieved_chunk_ids=["a", "c"],
    )
    result = await scorer(state, _make_target())
    assert result.value == 0.5


@pytest.mark.asyncio
async def test_recall_no_relevant() -> None:
    scorer = recall_at_k()
    state = _make_state(relevant_chunk_ids=[], retrieved_chunk_ids=["a"])
    result = await scorer(state, _make_target())
    assert result.value == 1.0  # vacuously true


@pytest.mark.asyncio
async def test_recall_none_retrieved() -> None:
    scorer = recall_at_k()
    state = _make_state(relevant_chunk_ids=["a", "b"], retrieved_chunk_ids=[])
    result = await scorer(state, _make_target())
    assert result.value == 0.0


# ── precision_at_k (legacy) ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_precision_perfect() -> None:
    scorer = precision_at_k()
    state = _make_state(
        relevant_chunk_ids=["a", "b"],
        retrieved_chunk_ids=["a", "b"],
    )
    result = await scorer(state, _make_target())
    assert result.value == 1.0


@pytest.mark.asyncio
async def test_precision_partial() -> None:
    scorer = precision_at_k()
    state = _make_state(
        relevant_chunk_ids=["a"],
        retrieved_chunk_ids=["a", "b", "c", "d"],
    )
    result = await scorer(state, _make_target())
    assert result.value == 0.25


@pytest.mark.asyncio
async def test_precision_no_retrieved() -> None:
    scorer = precision_at_k()
    state = _make_state(relevant_chunk_ids=["a"], retrieved_chunk_ids=[])
    result = await scorer(state, _make_target())
    assert result.value == 1.0  # vacuously true
