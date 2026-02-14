"""Retrieval - Unified retrieval package with runtime provider selection.

This package provides document retrieval capabilities with two backends:
- **basic**: Simple context injection (stuffs entire PDF into prompt)
- **albert**: Full RAG via Albert API (ingestion, search, reranking)

Backend selection is driven by `ragfacile.toml`:
    [storage]
    backend = "albert-collections"  # or "local-sqlite"

Example usage with factory:
    from retrieval import get_provider
    provider = get_provider()
    context = provider.process_file("document.pdf")

Backward-compatible imports (basic provider functions):
    from retrieval import extract_text_from_pdf, process_pdf_file
"""

from typing import Any


def get_provider(config: Any | None = None) -> Any:
    """Get the configured retrieval provider.

    Reads ragfacile.toml to determine which backend to load. Returns a
    module-like object with the standard retrieval interface.

    Args:
        config: Optional RAGConfig instance. If None, loads from ragfacile.toml.

    Returns:
        Provider module with retrieval functions (basic or albert backend).

    Raises:
        ValueError: If backend is not recognized.
    """
    if config is None:
        from rag_core import get_config

        config = get_config()

    # Determine backend from storage.backend config field
    backend = config.storage.backend

    if backend == "albert-collections":
        # Albert RAG: full pipeline with ingestion + search + reranking
        from . import albert, formatter, ingestion, parser

        # Return namespace with all albert functions
        return type(
            "AlbertProvider",
            (),
            {
                # Parser functions (backward compat with retrieval-basic API)
                "extract_text_from_pdf": parser.extract_text_from_pdf,
                "extract_text_from_bytes": parser.extract_text_from_bytes,
                "format_as_context": parser.format_as_context,
                "process_file": parser.process_file,
                "process_multiple_files": parser.process_multiple_files,
                "process_pdf_file": parser.process_pdf_file,
                "SUPPORTED_EXTENSIONS": parser.SUPPORTED_EXTENSIONS,
                "ACCEPTED_MIME_TYPES": parser.ACCEPTED_MIME_TYPES,
                # Retrieval functions
                "retrieve": albert.retrieve,
                "search_chunks": albert.search_chunks,
                "rerank_chunks": albert.rerank_chunks,
                # Ingestion functions
                "create_collection": ingestion.create_collection,
                "ingest_documents": ingestion.ingest_documents,
                "delete_collection": ingestion.delete_collection,
                "list_collections": ingestion.list_collections,
                # Formatting
                "format_context": formatter.format_context,
                "process_query": formatter.process_query,
            },
        )()
    elif backend == "local-sqlite":
        # Basic: simple context injection
        from . import basic

        return basic
    else:
        msg = f"Unknown storage backend: {backend}. Expected 'albert-collections' or 'local-sqlite'."
        raise ValueError(msg)


# Re-export common functions from basic provider for backward compatibility
# This allows: from retrieval import extract_text_from_pdf
from .basic import (  # noqa: E402
    ACCEPTED_MIME_TYPES,
    SUPPORTED_EXTENSIONS,
    extract_text_from_bytes,
    extract_text_from_pdf,
    format_as_context,
    process_file,
    process_multiple_files,
    process_pdf_file,
)

__all__ = [
    "get_provider",
    # Basic provider functions (backward compat)
    "extract_text_from_pdf",
    "extract_text_from_bytes",
    "format_as_context",
    "process_pdf_file",
    "process_file",
    "process_multiple_files",
    "SUPPORTED_EXTENSIONS",
    "ACCEPTED_MIME_TYPES",
]
