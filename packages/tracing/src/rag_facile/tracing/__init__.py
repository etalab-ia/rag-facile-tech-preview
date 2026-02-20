"""Tracing — RAG conversation logging and user feedback collection.

Records every RAG turn (question, retrieved chunks, injected prompt, LLM
answer, resolved model name, pipeline config, latency) to a local SQLite
database.  User feedback (star rating, quality tags, free-text comment) is
stored in a linked ``feedback`` table.

The database is created automatically at ``.rag-facile/traces.db`` in the
workspace root on first use.

Basic usage::

    from rag_facile.tracing import get_store

    store = get_store()
    store.record_turn({...})          # called by the pipeline
    store.record_feedback({...})      # called by the UI feedback handler

Export for RAGAS evaluation::

    samples = store.export_ragas(limit=200)
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._models import FeedbackRecord, TraceRecord
from ._store import TraceStore


if TYPE_CHECKING:
    pass


# ── Singleton store cache ──

_store: TraceStore | None = None
_lock = threading.Lock()


def get_store(config: Any | None = None) -> TraceStore:
    """Return the singleton :class:`TraceStore`, creating it on first call.

    The database path is taken from ``config.tracing.db_path``
    (default: ``.rag-facile/traces.db`` relative to the working directory).

    Args:
        config: Optional ``RAGConfig`` instance.  Loaded from
            ``ragfacile.toml`` if *None*.

    Returns:
        The shared :class:`TraceStore` instance.
    """
    global _store  # noqa: PLW0603
    if _store is None:
        with _lock:
            if _store is None:
                if config is None:
                    from rag_facile.core import get_config

                    config = get_config()
                db_path = Path(config.tracing.db_path)
                _store = TraceStore(db_path)
    assert _store is not None
    return _store


__all__ = [
    "FeedbackRecord",
    "TraceRecord",
    "TraceStore",
    "get_store",
]
