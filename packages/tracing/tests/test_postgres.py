"""Tests for the PostgresProvider.

Uses mocked psycopg connections to verify SQL generation and data
serialisation without requiring a running PostgreSQL instance.

For integration tests against real Postgres, set DATABASE_URL and run:
    pytest packages/tracing/tests/test_postgres.py -m integration
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from rag_facile.tracing._models import TraceRecord
from rag_facile.tracing.postgres import (
    PostgresProvider,
    _config_hash,
    _row_to_trace,
)


# ── Unit tests for helpers ────────────────────────────────────────────────────


class TestConfigHash:
    """Tests for _config_hash determinism."""

    def test_same_dict_same_hash(self):
        """Identical dicts produce identical hashes."""
        d = {"a": 1, "b": [2, 3]}
        assert _config_hash(d) == _config_hash(d)

    def test_key_order_irrelevant(self):
        """Dict key order doesn't affect the hash."""
        d1 = {"a": 1, "b": 2}
        d2 = {"b": 2, "a": 1}
        assert _config_hash(d1) == _config_hash(d2)

    def test_different_dicts_different_hash(self):
        """Different dicts produce different hashes."""
        assert _config_hash({"a": 1}) != _config_hash({"a": 2})


class TestRowToTrace:
    """Tests for _row_to_trace conversion."""

    def test_minimal_row(self):
        """A minimal row converts to a valid TraceRecord."""
        row = {
            "id": "test-id",
            "session_id": None,
            "user_id": None,
            "created_at": datetime(2026, 3, 10, tzinfo=timezone.utc),
            "response_at": None,
            "query": "What is RAG?",
            "expanded_queries": [],
            "retrieved_chunks": [],
            "reranked_chunks": [],
            "formatted_context": "",
            "collection_ids": [],
            "response": None,
            "model": "openweight-medium",
            "temperature": 0.2,
            "latency_ms": None,
            "config_hash": "abc123",
            "config": {"preset": "balanced"},
            "feedback_score": None,
            "feedback_tags": [],
            "feedback_comment": None,
        }
        trace = _row_to_trace(row)
        assert trace.id == "test-id"
        assert trace.query == "What is RAG?"
        assert trace.config_snapshot == {"preset": "balanced"}

    def test_json_string_columns_deserialized(self):
        """JSON columns stored as strings are correctly deserialized."""
        row = {
            "id": "test-id",
            "session_id": None,
            "user_id": None,
            "created_at": datetime(2026, 3, 10, tzinfo=timezone.utc),
            "response_at": None,
            "query": "test",
            "expanded_queries": '["q1", "q2"]',
            "retrieved_chunks": '[{"content": "chunk1"}]',
            "reranked_chunks": "[]",
            "formatted_context": "",
            "collection_ids": "[785]",
            "response": None,
            "model": "",
            "temperature": 0.0,
            "latency_ms": None,
            "config_hash": "abc",
            "config": '{"preset": "fast"}',
            "feedback_score": None,
            "feedback_tags": "[]",
            "feedback_comment": None,
        }
        trace = _row_to_trace(row)
        assert trace.expanded_queries == ["q1", "q2"]
        assert trace.retrieved_chunks[0]["content"] == "chunk1"
        assert trace.collection_ids == [785]
        assert trace.config_snapshot == {"preset": "fast"}

    def test_datetime_string_columns(self):
        """ISO datetime strings are converted to datetime objects."""
        row = {
            "id": "test-id",
            "session_id": None,
            "user_id": None,
            "created_at": "2026-03-10T12:00:00+00:00",
            "response_at": "2026-03-10T12:00:01+00:00",
            "query": "test",
            "expanded_queries": [],
            "retrieved_chunks": [],
            "reranked_chunks": [],
            "formatted_context": "",
            "collection_ids": [],
            "response": None,
            "model": "",
            "temperature": 0.0,
            "latency_ms": None,
            "config_hash": "abc",
            "config": {},
            "feedback_score": None,
            "feedback_tags": [],
            "feedback_comment": None,
        }
        trace = _row_to_trace(row)
        assert isinstance(trace.created_at, datetime)
        assert isinstance(trace.response_at, datetime)


# ── Unit tests for PostgresProvider (mocked) ──────────────────────────────────


class TestPostgresProviderInit:
    """Tests for provider initialization."""

    @patch("psycopg.connect")
    def test_init_verifies_connectivity(self, mock_connect):
        """Provider should execute SELECT 1 on init."""
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)

        PostgresProvider("postgresql://user:pass@host:5432/db")

        mock_conn.execute.assert_called_once_with("SELECT 1")

    @patch("psycopg.connect")
    def test_safe_conninfo_masks_password_uri(self, mock_connect):
        """The _safe_conninfo property should mask password in URI format."""
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)

        provider = PostgresProvider("postgresql://postgres:secret@host:5432/db")
        assert "secret" not in provider._safe_conninfo
        assert "****" in provider._safe_conninfo

    @patch("psycopg.connect")
    def test_safe_conninfo_masks_password_keyvalue(self, mock_connect):
        """The _safe_conninfo property should mask password in key-value format."""
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)

        provider = PostgresProvider(
            "host=localhost user=postgres password=secret dbname=db"
        )
        assert "secret" not in provider._safe_conninfo
        assert "****" in provider._safe_conninfo


class TestPostgresProviderLogTrace:
    """Tests for log_trace SQL generation."""

    @patch("psycopg.connect")
    def test_log_trace_inserts_config_and_trace(self, mock_connect):
        """log_trace should insert into both config_snapshots and traces."""
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)

        provider = PostgresProvider("postgresql://user:pass@host:5432/db")

        trace = TraceRecord(
            query="What is RAG?",
            model="openweight-medium",
            config_snapshot={"preset": "balanced"},
        )
        result = provider.log_trace(trace)

        assert result == trace.id
        # Should have: init SELECT 1, config upsert, trace insert, commit
        assert mock_conn.execute.call_count >= 2
        mock_conn.commit.assert_called()


class TestPostgresProviderUpdateTrace:
    """Tests for update_trace validation."""

    @patch("psycopg.connect")
    def test_update_rejects_invalid_columns(self, mock_connect):
        """update_trace should reject invalid column names."""
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)

        provider = PostgresProvider("postgresql://user:pass@host:5432/db")

        with pytest.raises(ValueError, match="Invalid field names"):
            provider.update_trace("trace-id", **{"malicious; DROP TABLE": "x"})

    @patch("psycopg.connect")
    def test_update_with_no_fields_is_noop(self, mock_connect):
        """update_trace with no fields should not execute any SQL."""
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)

        provider = PostgresProvider("postgresql://user:pass@host:5432/db")
        # Reset call count after init's SELECT 1
        mock_connect.reset_mock()

        provider.update_trace("trace-id")
        # No new connections should be opened for empty update
        mock_connect.assert_not_called()
