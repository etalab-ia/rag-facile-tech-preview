"""Tests for tracing module init — factory, contextvars, hook."""

from unittest.mock import MagicMock

import pytest

from rag_facile.tracing import (
    _notify_hook,
    _reset_tracer,
    get_current_trace_id,
    get_tracer,
    set_current_trace_id,
    set_trace_hook,
)
from rag_facile.tracing._models import TraceRecord
from rag_facile.tracing.noop import NoopProvider
from rag_facile.tracing.sqlite import SQLiteProvider


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset the tracer singleton before and after each test."""
    _reset_tracer()
    yield
    _reset_tracer()


class TestGetTracer:
    """Tests for the get_tracer() factory."""

    def test_returns_sqlite_by_default(self, tmp_path, monkeypatch):
        """When config has tracing.provider=sqlite, returns SQLiteProvider."""
        db_path = str(tmp_path / "traces.db")

        mock_config = MagicMock()
        mock_config.tracing.enabled = True
        mock_config.tracing.provider = "sqlite"
        mock_config.tracing.database = db_path

        tracer = get_tracer(mock_config)
        assert isinstance(tracer, SQLiteProvider)

    def test_returns_noop_when_disabled(self):
        """When tracing.enabled=false, returns NoopProvider."""
        mock_config = MagicMock()
        mock_config.tracing.enabled = False

        tracer = get_tracer(mock_config)
        assert isinstance(tracer, NoopProvider)

    def test_returns_noop_for_none_provider(self):
        """When tracing.provider=none, returns NoopProvider."""
        mock_config = MagicMock()
        mock_config.tracing.enabled = True
        mock_config.tracing.provider = "none"

        tracer = get_tracer(mock_config)
        assert isinstance(tracer, NoopProvider)

    def test_returns_postgres_provider(self, monkeypatch):
        """When tracing.provider=postgres with connection_string, returns PostgresProvider."""
        from unittest.mock import patch

        mock_config = MagicMock()
        mock_config.tracing.enabled = True
        mock_config.tracing.provider = "postgres"
        mock_config.tracing.connection_string = "postgresql://user:pass@host:5432/db"

        # Mock psycopg.connect so we don't need a real Postgres
        with patch("psycopg.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_connect.return_value.__exit__ = MagicMock(return_value=False)

            from rag_facile.tracing.postgres import PostgresProvider

            tracer = get_tracer(mock_config)
            assert isinstance(tracer, PostgresProvider)

    def test_postgres_falls_back_to_env_var(self, monkeypatch):
        """When connection_string is empty, reads DATABASE_URL env var."""
        from unittest.mock import patch

        mock_config = MagicMock()
        mock_config.tracing.enabled = True
        mock_config.tracing.provider = "postgres"
        mock_config.tracing.connection_string = ""

        monkeypatch.setenv("DATABASE_URL", "postgresql://env:pass@host:5432/db")

        with patch("psycopg.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_connect.return_value.__exit__ = MagicMock(return_value=False)

            from rag_facile.tracing.postgres import PostgresProvider

            tracer = get_tracer(mock_config)
            assert isinstance(tracer, PostgresProvider)

    def test_postgres_raises_without_connection_string(self, monkeypatch):
        """Postgres provider without connection string should raise ValueError."""
        mock_config = MagicMock()
        mock_config.tracing.enabled = True
        mock_config.tracing.provider = "postgres"
        mock_config.tracing.connection_string = ""

        monkeypatch.delenv("DATABASE_URL", raising=False)

        with pytest.raises(ValueError, match="connection string"):
            get_tracer(mock_config)

    def test_raises_for_unknown_provider(self):
        """Unknown provider should raise ValueError."""
        mock_config = MagicMock()
        mock_config.tracing.enabled = True
        mock_config.tracing.provider = "unknown"

        with pytest.raises(ValueError, match="Unknown tracing provider"):
            get_tracer(mock_config)

    def test_singleton_behavior(self, tmp_path):
        """get_tracer() should return the same instance on repeated calls."""
        db_path = str(tmp_path / "traces.db")
        mock_config = MagicMock()
        mock_config.tracing.enabled = True
        mock_config.tracing.provider = "sqlite"
        mock_config.tracing.database = db_path

        t1 = get_tracer(mock_config)
        t2 = get_tracer(mock_config)
        assert t1 is t2


class TestContextVars:
    """Tests for trace ID propagation via contextvars."""

    def test_default_is_none(self):
        """Current trace ID should default to None."""
        assert get_current_trace_id() is None

    def test_set_and_get(self):
        """Setting a trace ID should be retrievable."""
        set_current_trace_id("trace-abc")
        assert get_current_trace_id() == "trace-abc"

    def test_clear(self):
        """Setting to None should clear the trace ID."""
        set_current_trace_id("trace-abc")
        set_current_trace_id(None)
        assert get_current_trace_id() is None


class TestTraceHook:
    """Tests for the trace event hook mechanism."""

    def test_hook_called_with_trace(self):
        """The registered hook should be called with the trace record."""
        callback = MagicMock()
        set_trace_hook(callback)

        trace = TraceRecord(query="test hook")
        _notify_hook(trace)

        callback.assert_called_once_with(trace)

        # Cleanup
        set_trace_hook(None)

    def test_no_hook_does_not_raise(self):
        """Notifying without a hook should be a no-op."""
        set_trace_hook(None)
        trace = TraceRecord(query="test")
        _notify_hook(trace)  # should not raise
