"""Tests for the SQLite trace store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from rag_facile.tracing._models import FeedbackRecord, TraceRecord
from rag_facile.tracing._store import TraceStore


def _make_trace(trace_id: str | None = None, session_id: str = "sess-1") -> TraceRecord:
    return {
        "trace_id": trace_id or str(uuid4()),
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question": "Quels sont les droits des fonctionnaires ?",
        "chunks": json.dumps(
            [
                {
                    "content": "Art. 1...",
                    "score": 0.9,
                    "source_file": "loi.pdf",
                    "page": 1,
                    "collection_id": 42,
                    "document_id": 1,
                    "chunk_id": 10,
                }
            ]
        ),
        "prompt_sent": "Use the following context...\nQuestion: ...",
        "system_prompt": "You are a helpful assistant.",
        "answer": "Les fonctionnaires ont droit à...",
        "model_alias": "openweight-large",
        "model_resolved": "meta-llama/Llama-3.3-70B-Instruct",
        "preset": "balanced",
        "pipeline_config": json.dumps({"top_k": 10, "top_n": 5}),
        "latency_ms": 1234,
    }


def _make_feedback(trace_id: str) -> FeedbackRecord:
    return {
        "feedback_id": str(uuid4()),
        "trace_id": trace_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "star_rating": 4,
        "sentiment": "positive",
        "tags": ["Pertinent", "Clair"],
        "comment": "Très bonne réponse.",
    }


@pytest.fixture
def store(tmp_path: Path) -> TraceStore:
    return TraceStore(tmp_path / "traces.db")


# ── Basic CRUD ──


def test_record_turn_returns_trace_id(store: TraceStore) -> None:
    trace = _make_trace()
    result = store.record_turn(trace)
    assert result == trace["trace_id"]


def test_record_feedback(store: TraceStore) -> None:
    trace = _make_trace()
    store.record_turn(trace)
    fb = _make_feedback(trace["trace_id"])
    store.record_feedback(fb)  # must not raise


def test_recent_returns_traces(store: TraceStore) -> None:
    for _ in range(5):
        store.record_turn(_make_trace())
    rows = store.recent(n=3)
    assert len(rows) == 3


def test_recent_includes_feedback(store: TraceStore) -> None:
    trace = _make_trace()
    store.record_turn(trace)
    store.record_feedback(_make_feedback(trace["trace_id"]))
    rows = store.recent(n=1)
    assert rows[0]["star_rating"] == 4
    assert rows[0]["sentiment"] == "positive"


def test_recent_null_feedback_for_unrated(store: TraceStore) -> None:
    store.record_turn(_make_trace())
    rows = store.recent(n=1)
    assert rows[0]["star_rating"] is None


# ── RAGAS export ──


def test_export_ragas(store: TraceStore) -> None:
    trace = _make_trace()
    store.record_turn(trace)
    store.record_feedback(_make_feedback(trace["trace_id"]))
    samples = store.export_ragas(limit=10)
    assert len(samples) == 1
    s = samples[0]
    assert s["user_input"] == trace["question"]
    assert s["response"] == trace["answer"]
    assert isinstance(s["retrieved_contexts"], list)
    assert s["retrieved_contexts"][0] == "Art. 1..."
    assert s["_metadata"]["star_rating"] == 4


def test_export_ragas_empty_chunks(store: TraceStore) -> None:
    trace = _make_trace()
    trace["chunks"] = None
    store.record_turn(trace)
    samples = store.export_ragas()
    assert samples[0]["retrieved_contexts"] == []


# ── Stats ──


def test_stats(store: TraceStore) -> None:
    for _ in range(3):
        trace = _make_trace()
        store.record_turn(trace)
        store.record_feedback(_make_feedback(trace["trace_id"]))
    s = store.stats()
    assert s["total_traces"] == 3
    assert s["total_feedback"] == 3
    assert s["avg_star"] == 4.0
    assert any(tag == "Pertinent" for tag, _ in s["top_tags"])


# ── Prune ──


def test_prune_old_traces(store: TraceStore) -> None:
    old = _make_trace()
    old["created_at"] = "2020-01-01T00:00:00+00:00"
    store.record_turn(old)
    store.record_turn(_make_trace())  # recent
    deleted = store.prune(older_than_days=30)
    assert deleted == 1
    assert len(store.recent(n=100)) == 1


def test_prune_also_deletes_feedback(store: TraceStore) -> None:
    old = _make_trace()
    old["created_at"] = "2020-01-01T00:00:00+00:00"
    store.record_turn(old)
    store.record_feedback(_make_feedback(old["trace_id"]))
    store.prune(older_than_days=30)
    s = store.stats()
    assert s["total_feedback"] == 0


# ── Idempotency ──


def test_record_feedback_replace_on_duplicate(store: TraceStore) -> None:
    trace = _make_trace()
    store.record_turn(trace)
    fb = _make_feedback(trace["trace_id"])
    store.record_feedback(fb)
    fb["star_rating"] = 2  # update rating
    store.record_feedback(fb)  # same feedback_id → replace
    rows = store.recent(n=1)
    assert rows[0]["star_rating"] == 2
