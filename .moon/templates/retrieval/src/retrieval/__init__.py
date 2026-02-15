"""Retrieval - Search, reranking, and context formatting.

This package provides retrieval capabilities for the RAG pipeline:

- **Search**: Find relevant document chunks via Albert API
- **Reranking**: Re-score results with a cross-encoder for higher precision
- **Formatting**: Convert retrieved chunks into LLM-ready context strings

Example usage::

    from retrieval import retrieve, format_context

    chunks = retrieve(client, "What is RAG?", collection_ids=[1])
    context = format_context(chunks)

.. note::
    For file parsing and text extraction, use the ``ingestion`` package.
    For collection management (create, delete, list), use the ``storage`` package.
    For pipeline orchestration, use the ``pipelines`` package.
"""

from retrieval._types import RetrievedChunk
from retrieval.albert import rerank_chunks, retrieve, search_chunks
from retrieval.formatter import format_context, process_query


__all__ = [
    "RetrievedChunk",
    # Search & reranking
    "retrieve",
    "search_chunks",
    "rerank_chunks",
    # Context formatting
    "format_context",
    "process_query",
]
