"""Tests for the SQLiteProvider."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ragtime.tracing._models import TraceRecord
from ragtime.tracing.sqlite import SQLiteProvider


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Return a temporary database path."""
    return tmp_path / "traces.db"


@pytest.fixture
def provider(db_path: Path) -> SQLiteProvider:
    """Return a SQLiteProvider with a temporary database."""
    return SQLiteProvider(db_path)


class TestSQLiteProviderInit:
    """Tests for database initialisation."""

    def test_creates_database_file(self, db_path: Path):
        """Provider should create the database file on init."""
        SQLiteProvider(db_path)
        assert db_path.exists()

    def test_creates_parent_directories(self, tmp_path: Path):
        """Provider should create parent dirs if they don't exist."""
        deep_path = tmp_path / "a" / "b" / "traces.db"
        SQLiteProvider(deep_path)
        assert deep_path.exists()

    def test_wal_mode_enabled(self, db_path: Path):
        """Database should use WAL journal mode."""
        SQLiteProvider(db_path)
        conn = sqlite3.connect(str(db_path))
        mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        conn.close()
        assert mode == "wal"

    def test_traces_table_exists(self, db_path: Path):
        """The traces table should be created on init."""
        SQLiteProvider(db_path)
        conn = sqlite3.connect(str(db_path))
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='traces';"
        ).fetchall()
        conn.close()
        assert len(tables) == 1


class TestLogTrace:
    """Tests for log_trace."""

    def test_log_and_retrieve(self, provider: SQLiteProvider):
        """A logged trace should be retrievable by ID."""
        trace = TraceRecord(
            query="What is RAG?",
            model="openweight-medium",
            temperature=0.2,
            collection_ids=[785],
        )
        trace_id = provider.log_trace(trace)
        assert trace_id == trace.id

        retrieved = provider.get_trace(trace_id)
        assert retrieved is not None
        assert retrieved.query == "What is RAG?"
        assert retrieved.model == "openweight-medium"
        assert retrieved.temperature == pytest.approx(0.2)
        assert retrieved.collection_ids == [785]

    def test_log_with_chunks(self, provider: SQLiteProvider):
        """Chunks should be serialised and deserialised correctly."""
        chunks = [
            {"content": "Chunk 1", "score": 0.95, "source_file": "doc.pdf"},
            {"content": "Chunk 2", "score": 0.87, "source_file": "doc.pdf"},
        ]
        trace = TraceRecord(
            query="test",
            retrieved_chunks=chunks,
            reranked_chunks=chunks[:1],
        )
        provider.log_trace(trace)

        retrieved = provider.get_trace(trace.id)
        assert retrieved is not None
        assert len(retrieved.retrieved_chunks) == 2
        assert retrieved.retrieved_chunks[0]["content"] == "Chunk 1"
        assert len(retrieved.reranked_chunks) == 1

    def test_log_with_config_snapshot(self, provider: SQLiteProvider):
        """Config snapshot should be stored and retrieved as a dict."""
        config = {
            "meta": {"preset": "balanced"},
            "retrieval": {"top_k": 10, "strategy": "hybrid"},
        }
        trace = TraceRecord(query="test", config_snapshot=config)
        provider.log_trace(trace)

        retrieved = provider.get_trace(trace.id)
        assert retrieved is not None
        assert retrieved.config_snapshot["meta"]["preset"] == "balanced"
        assert retrieved.config_snapshot["retrieval"]["top_k"] == 10

    def test_config_snapshots_are_deduplicated(self, db_path: Path):
        """Identical configs should be stored only once in config_snapshots."""
        provider = SQLiteProvider(db_path)
        config = {"meta": {"preset": "balanced"}, "retrieval": {"top_k": 10}}

        # Log 3 traces with the same config
        for i in range(3):
            provider.log_trace(TraceRecord(query=f"q{i}", config_snapshot=config))

        # Verify: only 1 row in config_snapshots, 3 rows in traces
        conn = sqlite3.connect(str(db_path))
        config_rows = conn.execute("SELECT COUNT(*) FROM config_snapshots").fetchone()[
            0
        ]
        trace_rows = conn.execute("SELECT COUNT(*) FROM traces").fetchone()[0]
        conn.close()

        assert config_rows == 1, f"Expected 1 config row, got {config_rows}"
        assert trace_rows == 3

    def test_different_configs_stored_separately(self, db_path: Path):
        """Different configs should each get their own row."""
        provider = SQLiteProvider(db_path)

        provider.log_trace(
            TraceRecord(query="q1", config_snapshot={"preset": "balanced"})
        )
        provider.log_trace(TraceRecord(query="q2", config_snapshot={"preset": "fast"}))

        conn = sqlite3.connect(str(db_path))
        config_rows = conn.execute("SELECT COUNT(*) FROM config_snapshots").fetchone()[
            0
        ]
        conn.close()

        assert config_rows == 2


class TestUpdateTrace:
    """Tests for update_trace."""

    def test_update_response(self, provider: SQLiteProvider):
        """Updating response and latency should persist."""
        trace = TraceRecord(query="test")
        provider.log_trace(trace)

        now = datetime.now(timezone.utc)
        provider.update_trace(
            trace.id,
            response="RAG stands for Retrieval-Augmented Generation.",
            latency_ms=1500,
            response_at=now,
        )

        updated = provider.get_trace(trace.id)
        assert updated is not None
        assert updated.response == "RAG stands for Retrieval-Augmented Generation."
        assert updated.latency_ms == 1500
        assert updated.response_at is not None

    def test_update_session_and_user(self, provider: SQLiteProvider):
        """Session and user IDs can be set after creation."""
        trace = TraceRecord(query="test")
        provider.log_trace(trace)

        provider.update_trace(
            trace.id,
            session_id="session-abc",
            user_id="user-42",
        )

        updated = provider.get_trace(trace.id)
        assert updated is not None
        assert updated.session_id == "session-abc"
        assert updated.user_id == "user-42"

    def test_update_with_no_fields(self, provider: SQLiteProvider):
        """Updating with no fields should be a no-op."""
        trace = TraceRecord(query="test")
        provider.log_trace(trace)
        provider.update_trace(trace.id)  # should not raise

    def test_update_rejects_invalid_column(self, provider: SQLiteProvider):
        """Passing an invalid column name should raise ValueError."""
        trace = TraceRecord(query="test")
        provider.log_trace(trace)

        with pytest.raises(ValueError, match="Invalid field names"):
            provider.update_trace(trace.id, **{"malicious; DROP TABLE traces": "x"})


class TestAddFeedback:
    """Tests for add_feedback."""

    def test_add_score(self, provider: SQLiteProvider):
        """Adding a feedback score should persist."""
        trace = TraceRecord(query="test")
        provider.log_trace(trace)

        provider.add_feedback(trace.id, score=5)

        updated = provider.get_trace(trace.id)
        assert updated is not None
        assert updated.feedback_score == 5

    def test_add_tags_and_comment(self, provider: SQLiteProvider):
        """Adding tags and comment should persist."""
        trace = TraceRecord(query="test")
        provider.log_trace(trace)

        provider.add_feedback(
            trace.id,
            tags=["irrelevant", "incomplete"],
            comment="Not what I was looking for",
        )

        updated = provider.get_trace(trace.id)
        assert updated is not None
        assert "irrelevant" in updated.feedback_tags
        assert updated.feedback_comment == "Not what I was looking for"

    def test_add_feedback_with_no_values(self, provider: SQLiteProvider):
        """Calling add_feedback with no values should be a no-op."""
        trace = TraceRecord(query="test")
        provider.log_trace(trace)
        provider.add_feedback(trace.id)  # should not raise


class TestListTraces:
    """Tests for list_traces."""

    def test_list_empty(self, provider: SQLiteProvider):
        """Listing with no traces should return empty list."""
        assert provider.list_traces() == []

    def test_list_returns_newest_first(self, provider: SQLiteProvider):
        """Traces should be returned newest first."""
        t1 = TraceRecord(id="first", query="q1")
        t2 = TraceRecord(id="second", query="q2")
        provider.log_trace(t1)
        provider.log_trace(t2)

        traces = provider.list_traces()
        assert len(traces) == 2
        assert traces[0].id == "second"
        assert traces[1].id == "first"

    def test_filter_by_session(self, provider: SQLiteProvider):
        """Filtering by session_id should return only matching traces."""
        t1 = TraceRecord(query="q1", session_id="s1")
        t2 = TraceRecord(query="q2", session_id="s2")
        provider.log_trace(t1)
        provider.log_trace(t2)

        traces = provider.list_traces(session_id="s1")
        assert len(traces) == 1
        assert traces[0].session_id == "s1"

    def test_filter_by_user(self, provider: SQLiteProvider):
        """Filtering by user_id should return only matching traces."""
        t1 = TraceRecord(query="q1", user_id="u1")
        t2 = TraceRecord(query="q2", user_id="u2")
        provider.log_trace(t1)
        provider.log_trace(t2)

        traces = provider.list_traces(user_id="u1")
        assert len(traces) == 1
        assert traces[0].user_id == "u1"

    def test_limit_and_offset(self, provider: SQLiteProvider):
        """Pagination should work correctly."""
        for i in range(5):
            provider.log_trace(TraceRecord(query=f"q{i}"))

        page1 = provider.list_traces(limit=2, offset=0)
        assert len(page1) == 2

        page2 = provider.list_traces(limit=2, offset=2)
        assert len(page2) == 2

        page3 = provider.list_traces(limit=2, offset=4)
        assert len(page3) == 1


class TestGetTrace:
    """Tests for get_trace."""

    def test_nonexistent_trace(self, provider: SQLiteProvider):
        """Getting a nonexistent trace should return None."""
        assert provider.get_trace("nonexistent") is None

    def test_datetime_roundtrip(self, provider: SQLiteProvider):
        """Datetime fields should survive serialisation roundtrip."""
        now = datetime.now(timezone.utc)
        trace = TraceRecord(
            query="test",
            created_at=now,
            response_at=now,
        )
        provider.log_trace(trace)

        retrieved = provider.get_trace(trace.id)
        assert retrieved is not None
        assert retrieved.created_at.isoformat() == now.isoformat()
        assert retrieved.response_at is not None
        assert retrieved.response_at.isoformat() == now.isoformat()


class TestSchemaMigration:
    """Tests for old → new schema migration (config_snapshot → config_hash)."""

    def test_migrates_old_schema(self, tmp_path: Path):
        """A database with the old config_snapshot column should be migrated."""
        db_path = tmp_path / "old.db"

        # 1. Create a database with the OLD schema
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("""
            CREATE TABLE traces (
                id TEXT PRIMARY KEY,
                session_id TEXT, user_id TEXT,
                created_at TEXT NOT NULL, response_at TEXT,
                query TEXT NOT NULL DEFAULT '',
                expanded_queries TEXT NOT NULL DEFAULT '[]',
                retrieved_chunks TEXT NOT NULL DEFAULT '[]',
                reranked_chunks TEXT NOT NULL DEFAULT '[]',
                formatted_context TEXT NOT NULL DEFAULT '',
                collection_ids TEXT NOT NULL DEFAULT '[]',
                response TEXT, model TEXT NOT NULL DEFAULT '',
                temperature REAL NOT NULL DEFAULT 0.0,
                latency_ms INTEGER,
                config_snapshot TEXT NOT NULL DEFAULT '{}',
                feedback_score INTEGER,
                feedback_tags TEXT NOT NULL DEFAULT '[]',
                feedback_comment TEXT
            );
        """)
        config = '{"meta": {"preset": "balanced"}}'
        conn.execute(
            "INSERT INTO traces (id, created_at, query, config_snapshot) "
            "VALUES (?, ?, ?, ?)",
            ("old-1", "2026-02-24T10:00:00+00:00", "test query", config),
        )
        conn.commit()
        conn.close()

        # 2. Open with the new SQLiteProvider — should auto-migrate
        provider = SQLiteProvider(db_path)

        # 3. Verify the old trace is readable with config_snapshot reconstructed
        trace = provider.get_trace("old-1")
        assert trace is not None
        assert trace.query == "test query"
        assert trace.config_snapshot["meta"]["preset"] == "balanced"

        # 4. Verify config_snapshot column is gone, config_hash exists
        conn = sqlite3.connect(str(db_path))
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(traces);").fetchall()
        }
        conn.close()
        assert "config_hash" in columns
        assert "config_snapshot" not in columns
