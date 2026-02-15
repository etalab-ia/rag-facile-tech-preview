"""Albert RAG pipeline — full retrieval with Albert API.

Parses documents via the Albert API (ingestion package) and supports
query-time retrieval with search, reranking, and context formatting.
Orchestrates the individual phase packages.

Selected when ``storage.provider = "albert-collections"`` in ragfacile.toml.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._base import RAGPipeline


if TYPE_CHECKING:
    from albert import AlbertClient


class AlbertPipeline(RAGPipeline):
    """Full RAG pipeline using the Albert API.

    File processing is delegated to the ingestion package.
    Collection management is delegated to the storage package.
    Query-time retrieval orchestrates: search → rerank → format
    using the retrieval, reranking, and context packages.
    """

    def __init__(self, config: Any | None = None) -> None:
        from ingestion import get_provider
        from storage import get_provider as get_storage_provider

        self._ingestion = get_provider(config)
        self._storage = get_storage_provider(config)

    # ── Upload-time: file processing ──

    def process_file(
        self,
        path: str | Path,
        filename: str | None = None,
    ) -> str:
        """Parse a file via Albert API and return formatted context."""
        return self._ingestion.process_file(path, filename)

    def process_bytes(self, data: bytes, filename: str) -> str:
        """Parse file bytes via Albert API and return formatted context."""
        return self._ingestion.process_bytes(data, filename)

    # ── Query-time: search → rerank → format ──

    def process_query(
        self,
        query: str,
        **kwargs: object,
    ) -> str:
        """Retrieve relevant context from Albert collections.

        Orchestrates the full retrieval pipeline:
        1. Search for relevant chunks (retrieval package)
        2. Optionally rerank results (reranking package)
        3. Format chunks as LLM context (context package)

        All parameters default to ragfacile.toml config values.

        Args:
            query: User query to retrieve context for.
            **kwargs: Pipeline options.
                ``collection_ids`` (required): Albert collection IDs to search.
                ``client``: Optional pre-configured Albert client.

        Returns:
            Formatted context string ready for LLM injection.
        """
        from context import format_context
        from rag_core import get_config
        from reranking import rerank_chunks
        from retrieval import search_chunks

        config = get_config()

        # Resolve client
        client: AlbertClient | None = kwargs.get("client")  # type: ignore[assignment]
        if client is None:
            from albert import AlbertClient as _AlbertClient

            client = _AlbertClient()

        try:
            collection_ids: list[int | str] = kwargs["collection_ids"]  # type: ignore[assignment]
        except KeyError:
            raise ValueError(
                "`collection_ids` is a required argument for `process_query`."
            ) from None

        # Step 1: Search
        chunks = search_chunks(
            client,
            query,
            collection_ids,
            limit=config.retrieval.top_k,
            method=config.retrieval.strategy,
            score_threshold=config.retrieval.score_threshold,
        )

        if not chunks:
            return ""

        # Step 2: Rerank (optional)
        if config.reranking.enabled:
            chunks = rerank_chunks(
                client,
                query,
                chunks,
                model=config.reranking.model,
                top_n=config.reranking.top_n,
            )

        # Step 3: Format as LLM context
        return format_context(chunks)

    # ── Collection management (delegated to storage) ──

    def create_collection(
        self,
        client: AlbertClient,
        name: str,
        description: str = "",
    ) -> int:
        """Create a new collection in Albert.

        Args:
            client: Configured Albert client.
            name: Collection name.
            description: Optional description.

        Returns:
            The new collection ID.
        """
        return self._storage.create_collection(client, name, description)

    def ingest_documents(
        self,
        client: AlbertClient,
        paths: list[str | Path],
        collection_id: int,
        *,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> list[int]:
        """Upload documents to an Albert collection for indexing.

        Args:
            client: Configured Albert client.
            paths: Document file paths to upload.
            collection_id: Target collection ID.
            chunk_size: Override chunk size (defaults to config).
            chunk_overlap: Override chunk overlap (defaults to config).

        Returns:
            List of document IDs created.
        """
        return self._storage.ingest_documents(
            client,
            paths,
            collection_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def delete_collection(self, client: AlbertClient, collection_id: int) -> None:
        """Delete a collection and all its documents.

        Args:
            client: Configured Albert client.
            collection_id: Collection to delete.
        """
        self._storage.delete_collection(client, collection_id)

    def list_collections(
        self,
        client: AlbertClient,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> Any:
        """List accessible collections.

        Args:
            client: Configured Albert client.
            limit: Maximum number of results.
            offset: Pagination offset.

        Returns:
            CollectionList from Albert API.
        """
        return self._storage.list_collections(client, limit=limit, offset=offset)

    # ── Capabilities ──

    @property
    def supported_extensions(self) -> list[str]:
        """File extensions supported by the Albert ingestion provider."""
        return self._ingestion.supported_extensions

    @property
    def accepted_mime_types(self) -> dict[str, list[str]]:
        """MIME types accepted by the Albert ingestion provider."""
        return self._ingestion.accepted_mime_types
