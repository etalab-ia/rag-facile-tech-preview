"""Tests for the NoopProvider."""

from ragtime.tracing._models import TraceRecord
from ragtime.tracing.noop import NoopProvider


class TestNoopProvider:
    """Tests for NoopProvider — all writes are no-ops, all reads return empty."""

    def test_log_trace_returns_id(self):
        """log_trace should return the trace ID even though nothing is stored."""
        provider = NoopProvider()
        trace = TraceRecord(id="noop-1", query="test")
        result = provider.log_trace(trace)
        assert result == "noop-1"

    def test_get_trace_returns_none(self):
        """get_trace should always return None."""
        provider = NoopProvider()
        assert provider.get_trace("any-id") is None

    def test_list_traces_returns_empty(self):
        """list_traces should always return an empty list."""
        provider = NoopProvider()
        assert provider.list_traces() == []
        assert provider.list_traces(session_id="s1") == []
        assert provider.list_traces(user_id="u1") == []

    def test_update_trace_is_noop(self):
        """update_trace should not raise."""
        provider = NoopProvider()
        provider.update_trace("any-id", response="hello")  # should not raise

    def test_add_feedback_is_noop(self):
        """add_feedback should not raise."""
        provider = NoopProvider()
        provider.add_feedback("any-id", score=5, tags=["good"])  # should not raise
