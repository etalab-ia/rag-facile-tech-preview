"""Pytest configuration and shared fixtures for context tests."""

import pytest

from rag_core.schema import (
    CitationsConfig,
    FormattingConfig,
    RAGConfig,
)


@pytest.fixture
def mock_config(monkeypatch):
    """Patch rag_core.get_config() with test values."""
    config = RAGConfig(
        formatting=FormattingConfig(
            citations=CitationsConfig(enabled=True, style="inline")
        ),
    )
    monkeypatch.setattr("context.formatter.get_config", lambda: config)
    return config
