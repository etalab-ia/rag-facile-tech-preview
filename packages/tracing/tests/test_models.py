"""Tests for tracing data models."""

from datetime import datetime, timezone

from ragtime.tracing._models import FeedbackUpdate, TraceRecord


class TestTraceRecord:
    """Tests for TraceRecord dataclass."""

    def test_default_creation(self):
        """TraceRecord should have sensible defaults."""
        trace = TraceRecord()
        assert trace.id  # UUID generated
        assert trace.query == ""
        assert trace.session_id is None
        assert trace.user_id is None
        assert trace.response is None
        assert trace.feedback_score is None
        assert trace.expanded_queries == []
        assert trace.retrieved_chunks == []
        assert trace.config_snapshot == {}
        assert isinstance(trace.created_at, datetime)

    def test_creation_with_values(self):
        """TraceRecord should accept all fields."""
        now = datetime.now(timezone.utc)
        trace = TraceRecord(
            id="test-123",
            session_id="session-1",
            user_id="user-42",
            created_at=now,
            query="What is RAG?",
            expanded_queries=["query 1", "query 2"],
            retrieved_chunks=[{"content": "chunk", "score": 0.9}],
            reranked_chunks=[{"content": "chunk", "score": 0.95}],
            formatted_context="Context: chunk",
            collection_ids=[785, 784],
            response="RAG stands for...",
            model="openweight-medium",
            temperature=0.2,
            latency_ms=1500,
            config_snapshot={"meta": {"preset": "balanced"}},
            feedback_score=5,
            feedback_tags=["helpful"],
            feedback_comment="Great answer!",
        )
        assert trace.id == "test-123"
        assert trace.session_id == "session-1"
        assert trace.query == "What is RAG?"
        assert len(trace.expanded_queries) == 2
        assert trace.collection_ids == [785, 784]
        assert trace.feedback_score == 5

    def test_unique_ids(self):
        """Each TraceRecord should get a unique ID."""
        t1 = TraceRecord()
        t2 = TraceRecord()
        assert t1.id != t2.id


class TestFeedbackUpdate:
    """Tests for FeedbackUpdate dataclass."""

    def test_default_creation(self):
        """FeedbackUpdate should have None defaults."""
        update = FeedbackUpdate()
        assert update.score is None
        assert update.tags == []
        assert update.comment is None

    def test_with_values(self):
        """FeedbackUpdate should accept all fields."""
        update = FeedbackUpdate(
            score=4,
            tags=["relevant", "well-cited"],
            comment="Good but could be more detailed",
        )
        assert update.score == 4
        assert "relevant" in update.tags
