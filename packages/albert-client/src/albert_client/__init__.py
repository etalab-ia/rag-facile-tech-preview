"""Albert Client - Official Python SDK for France's Albert API.

A sovereign AI platform providing OpenAI-compatible endpoints plus
French government-specific features like RAG search, collections management,
and carbon footprint tracking.
"""

from albert_client._async_client import AsyncAlbertClient
from albert_client._version import __version__
from albert_client.client import AlbertClient
from albert_client.types import (
    Chunk,
    RerankResponse,
    RerankResult,
    SearchMethod,
    SearchResponse,
    SearchResult,
    Usage,
)

__all__ = [
    # Clients
    "AlbertClient",
    "AsyncAlbertClient",
    # Search & Rerank types
    "Chunk",
    "RerankResult",
    "RerankResponse",
    "SearchMethod",
    "SearchResult",
    "SearchResponse",
    "Usage",
    # Metadata
    "__version__",
]
