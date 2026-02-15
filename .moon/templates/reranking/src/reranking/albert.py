"""Albert-powered reranking via cross-encoder models.

Provides config-driven reranking that wraps the Albert client SDK.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rag_core import RetrievedChunk


if TYPE_CHECKING:
    from albert import AlbertClient


logger = logging.getLogger(__name__)


def rerank_chunks(
    client: AlbertClient,
    query: str,
    chunks: list[RetrievedChunk],
    *,
    model: str = "openweight-rerank",
    top_n: int | None = None,
) -> list[RetrievedChunk]:
    """Rerank chunks by relevance to a query.

    Args:
        client: Authenticated Albert client.
        query: The query to rank chunks against.
        chunks: Chunks to rerank.
        model: Reranker model name.
        top_n: Return only top N results. If None, returns all.

    Returns:
        Reranked list of chunks (highest relevance first).
    """
    if not chunks:
        return []

    documents = [c["content"] for c in chunks]
    response = client.rerank(
        query=query,
        documents=documents,
        model=model,
        top_n=top_n,
    )

    # Build reranked list using the results index mapping
    reranked: list[RetrievedChunk] = []
    for result in response.results:
        original = chunks[result.index]
        reranked.append(
            RetrievedChunk(
                content=original["content"],
                score=result.relevance_score,
                source_file=original["source_file"],
                page=original["page"],
                collection_id=original["collection_id"],
                document_id=original["document_id"],
                chunk_id=original["chunk_id"],
            )
        )

    logger.info("Reranked %d chunks → %d results", len(chunks), len(reranked))
    return reranked
