"""Reranking - re-score retrieved chunks with a cross-encoder.

This package provides pluggable reranking capabilities for the RAG pipeline.
The provider is selected via ``ragtime.toml``::

    [reranking]
    enabled = true
    provider = "albert"
    model = "openweight-rerank"
    top_n = 5

Example usage::

    from ragtime.reranking import get_provider

    reranking = get_provider()
    if reranking:
        reranked = reranking.rerank("What is RAG?", chunks)

.. note::
    For vector search, use the ``retrieval`` package.
    For context formatting, use the ``context`` package.
"""

from __future__ import annotations

from typing import Any

from ragtime.reranking._base import RerankingProvider
from ragtime.reranking.albert import AlbertRerankingProvider


def get_provider(config: Any | None = None) -> RerankingProvider | None:
    """Get the configured reranking provider.

    Reads ``reranking.enabled`` and ``reranking.provider`` from
    ``ragtime.toml`` (or the supplied *config*).  Returns ``None`` when
    reranking is disabled — the pipeline will skip the reranking phase.

    Args:
        config: Optional :class:`~ragtime.core.RAGConfig` instance.
            If ``None``, loads configuration from ``ragtime.toml``.

    Returns:
        A :class:`RerankingProvider` instance, or ``None`` when
        ``reranking.enabled = false``.

    Raises:
        ValueError: If the configured provider is not recognised.
    """
    if config is None:
        from ragtime.core import get_config

        config = get_config()

    if not config.reranking.enabled:
        return None

    provider = config.reranking.provider

    match provider:
        case "albert":
            return AlbertRerankingProvider(
                model=config.reranking.model,
                top_n=config.reranking.top_n,
            )
        case _:
            msg = f"Unknown reranking provider: {provider!r}. Expected 'albert'."
            raise ValueError(msg)


__all__ = [
    "AlbertRerankingProvider",
    "RerankingProvider",
    "get_provider",
]
