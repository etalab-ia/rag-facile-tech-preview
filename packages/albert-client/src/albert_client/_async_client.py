"""Async Albert Client implementation."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from openai import AsyncOpenAI

if TYPE_CHECKING:
    from pathlib import Path

    from albert_client.types import (
        Chunk,
        ChunkList,
        Collection,
        CollectionList,
        CollectionVisibility,
        Document,
        DocumentList,
        RerankResponse,
        SearchResponse,
    )


class AsyncAlbertClient:
    """Async version of Albert Client.

    Provides the same interface as AlbertClient but with async/await support.

    Example:
        ```python
        from albert_client import AsyncAlbertClient

        # Initialize async client
        client = AsyncAlbertClient(
            api_key="albert_...",
            base_url="https://albert.api.etalab.gouv.fr/v1"
        )

        # OpenAI-compatible endpoints
        response = await client.chat.completions.create(
            model="AgentPublic/llama3-instruct-8b",
            messages=[{"role": "user", "content": "Hello!"}]
        )

        # Albert-specific endpoints (coming in Phase 2+)
        # results = await client.search(prompt="...", collections=["..."])
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://albert.api.etalab.gouv.fr/v1",
        **kwargs,
    ):
        """Initialize async Albert client.

        Args:
            api_key: Albert API key. If not provided, reads from ALBERT_API_KEY env var.
            base_url: Base URL for Albert API (includes /v1 suffix).
            **kwargs: Additional arguments passed to AsyncOpenAI client.
        """
        # Get API key from env if not provided
        if api_key is None:
            api_key = os.environ.get("ALBERT_API_KEY")

        if not api_key:
            raise ValueError(
                "Albert API key is required. Provide via api_key parameter or "
                "ALBERT_API_KEY environment variable."
            )

        # Initialize wrapped AsyncOpenAI client
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url, **kwargs)

        # OpenAI-Compatible Passthrough
        self.chat = self._client.chat
        self.embeddings = self._client.embeddings
        self.audio = self._client.audio
        self.models = self._client.models

        # Albert-Specific Resources (will be implemented in Phase 2+)
        # self.collections = AsyncCollections(self._client)
        # self.documents = AsyncDocuments(self._client)
        # self.tools = AsyncTools(self._client)
        # self.management = AsyncManagement(self._client)

    @property
    def api_key(self) -> str:
        """Get the API key."""
        return self._client.api_key

    @property
    def base_url(self) -> str:
        """Get the base URL."""
        return str(self._client.base_url)

    async def close(self) -> None:
        """Close the underlying httpx client."""
        await self._client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    # Phase 2: Search and Rerank async methods

    async def search(
        self,
        prompt: str,
        collections: list[str | int] | None = None,
        limit: int = 10,
        offset: int = 0,
        method: str = "semantic",
        score_threshold: float | None = None,
        rff_k: int = 20,
    ) -> SearchResponse:
        """Async hybrid RAG search across collections.

        Searches for relevant chunks in the specified collections using the given prompt.
        Supports semantic, lexical, or hybrid search methods.

        Args:
            prompt: Search query to find relevant chunks.
            collections: List of collection IDs to search in. Defaults to all collections.
            limit: Maximum number of results to return (1-200). Defaults to 10.
            offset: Pagination offset. Defaults to 0.
            method: Search method - "semantic", "lexical", or "hybrid". Defaults to "semantic".
            score_threshold: Minimum cosine similarity score (0.0-1.0). Only for semantic search.
            rff_k: RFF algorithm constant. Defaults to 20.

        Returns:
            SearchResponse with results, usage info, and metadata.

        Raises:
            httpx.HTTPStatusError: If the API request fails.

        Example:
            ```python
            async with AsyncAlbertClient(api_key="albert_...") as client:
                results = await client.search(
                    prompt="Loi Énergie Climat",
                    collections=["col_123"],
                    limit=5,
                    method="hybrid"
                )
                for result in results.data:
                    print(f"Score: {result.score:.3f}")
            ```
        """
        from albert_client.types import SearchResponse

        # Build request body
        body = {
            "prompt": prompt,
            "collections": collections or [],
            "limit": limit,
            "offset": offset,
            "method": method,
            "rff_k": rff_k,
        }
        if score_threshold is not None:
            body["score_threshold"] = score_threshold

        # Make request using internal httpx client
        response = await self._client._client.post("/search", json=body)
        response.raise_for_status()

        # Parse and return Pydantic model
        return SearchResponse(**response.json())

    async def rerank(
        self,
        query: str,
        documents: list[str],
        model: str,
        top_n: int | None = None,
    ) -> RerankResponse:
        """Async rerank documents by relevance to a query.

        Takes a list of documents and reorders them by relevance to the query.
        Useful for improving RAG retrieval quality.

        Args:
            query: The search query to rank documents against.
            documents: List of document texts to rerank.
            model: Reranker model to use (e.g., "BAAI/bge-reranker-v2-m3").
            top_n: Return only top N results. If None, returns all documents.

        Returns:
            RerankResponse with reranked results and scores.

        Raises:
            httpx.HTTPStatusError: If the API request fails.

        Example:
            ```python
            async with AsyncAlbertClient(api_key="albert_...") as client:
                results = await client.rerank(
                    query="transition énergétique",
                    documents=["doc1", "doc2", "doc3"],
                    model="BAAI/bge-reranker-v2-m3",
                    top_n=2
                )
            ```
        """
        from albert_client.types import RerankResponse

        # Build request body
        body = {
            "query": query,
            "documents": documents,
            "model": model,
        }
        if top_n is not None:
            body["top_n"] = top_n

        # Make request using internal httpx client
        response = await self._client._client.post("/rerank", json=body)
        response.raise_for_status()

        # Parse and return Pydantic model
        return RerankResponse(**response.json())

    # Phase 3: Collections methods (async)

    async def create_collection(
        self,
        name: str,
        description: str | None = None,
        visibility: CollectionVisibility = "private",
    ) -> Collection:
        """Create a new RAG collection (async).

        Collections organize documents for semantic search. Each collection has its
        own embedding model and access permissions.

        Args:
            name: Name of the collection (required).
            description: Optional description of the collection.
            visibility: "private" (owner only) or "public" (all users). Defaults to "private".

        Returns:
            Collection object with ID and metadata.

        Raises:
            httpx.HTTPStatusError: If the API request fails.

        Example:
            ```python
            async with AsyncAlbertClient(api_key="albert_...") as client:
                collection = await client.create_collection(
                    name="French Legal Documents",
                    visibility="private"
                )
            ```
        """
        from albert_client.types import Collection

        body = {"name": name, "visibility": visibility}
        if description is not None:
            body["description"] = description

        response = await self._client._client.post("/collections", json=body)
        response.raise_for_status()

        return Collection(**response.json())

    async def list_collections(self) -> CollectionList:
        """List all accessible collections (async).

        Returns collections owned by the user plus any public collections.

        Returns:
            CollectionList containing all accessible collections.

        Raises:
            httpx.HTTPStatusError: If the API request fails.

        Example:
            ```python
            async with AsyncAlbertClient(api_key="albert_...") as client:
                collections = await client.list_collections()
                for collection in collections.data:
                    print(f"{collection.name}: {collection.documents} documents")
            ```
        """
        from albert_client.types import CollectionList

        response = await self._client._client.get("/collections")
        response.raise_for_status()

        return CollectionList(**response.json())

    async def get_collection(self, collection_id: int) -> Collection:
        """Get a specific collection by ID (async).

        Args:
            collection_id: The collection ID.

        Returns:
            Collection object with full metadata.

        Raises:
            httpx.HTTPStatusError: If the collection doesn't exist or isn't accessible.

        Example:
            ```python
            async with AsyncAlbertClient(api_key="albert_...") as client:
                collection = await client.get_collection(123)
            ```
        """
        from albert_client.types import Collection

        response = await self._client._client.get(f"/collections/{collection_id}")
        response.raise_for_status()

        return Collection(**response.json())

    async def update_collection(
        self,
        collection_id: int,
        name: str | None = None,
        description: str | None = None,
        visibility: CollectionVisibility | None = None,
    ) -> Collection:
        """Update a collection's metadata (async).

        Only the collection owner can update it. At least one field must be provided.

        Args:
            collection_id: The collection ID to update.
            name: New name for the collection (optional).
            description: New description (optional).
            visibility: New visibility setting (optional).

        Returns:
            Updated Collection object.

        Raises:
            httpx.HTTPStatusError: If the update fails or user lacks permission.
        """
        from albert_client.types import Collection

        body = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if visibility is not None:
            body["visibility"] = visibility

        response = await self._client._client.patch(f"/collections/{collection_id}", json=body)
        response.raise_for_status()

        return Collection(**response.json())

    async def delete_collection(self, collection_id: int) -> None:
        """Delete a collection and all its documents (async).

        Only the collection owner can delete it. This action is irreversible.

        Args:
            collection_id: The collection ID to delete.

        Raises:
            httpx.HTTPStatusError: If the deletion fails or user lacks permission.
        """
        response = await self._client._client.delete(f"/collections/{collection_id}")
        response.raise_for_status()

    # Phase 3: Documents methods (async)

    async def upload_document(
        self,
        file_path: str | Path,
        collection_id: int,
        chunk_size: int = 2048,
        chunk_overlap: int = 0,
        **kwargs,
    ) -> Document:
        """Upload a document to a collection (async).

        The document will be parsed, chunked, and embedded according to the collection's
        settings. Supports PDF, DOCX, TXT, and other common formats.

        Args:
            file_path: Path to the file to upload.
            collection_id: The collection ID to add the document to.
            chunk_size: Size of text chunks for embedding (default: 2048).
            chunk_overlap: Overlap between chunks (default: 0).
            **kwargs: Additional upload parameters (page_range, force_ocr, etc.).

        Returns:
            Document object with ID and metadata.

        Raises:
            httpx.HTTPStatusError: If the upload fails.

        Example:
            ```python
            async with AsyncAlbertClient(api_key="albert_...") as client:
                doc = await client.upload_document(
                    file_path="./legal_doc.pdf",
                    collection_id=123,
                    chunk_size=1024
                )
            ```
        """
        from pathlib import Path

        from albert_client.types import Document

        file_path = Path(file_path)

        form_data = {
            "collection": collection_id,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }
        form_data.update(kwargs)

        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/octet-stream")}
            response = await self._client._client.post("/documents", data=form_data, files=files)
            response.raise_for_status()

        return Document(**response.json())

    async def list_documents(self, collection_id: int | None = None) -> DocumentList:
        """List documents in a collection or all accessible documents (async).

        Args:
            collection_id: Filter to specific collection. If None, returns all accessible documents.

        Returns:
            DocumentList containing matching documents.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        from albert_client.types import DocumentList

        params = {}
        if collection_id is not None:
            params["collection"] = collection_id

        response = await self._client._client.get("/documents", params=params)
        response.raise_for_status()

        return DocumentList(**response.json())

    async def get_document(self, document_id: int) -> Document:
        """Get a specific document by ID (async).

        Args:
            document_id: The document ID.

        Returns:
            Document object with metadata.

        Raises:
            httpx.HTTPStatusError: If the document doesn't exist or isn't accessible.
        """
        from albert_client.types import Document

        response = await self._client._client.get(f"/documents/{document_id}")
        response.raise_for_status()

        return Document(**response.json())

    async def delete_document(self, document_id: int) -> None:
        """Delete a document and all its chunks (async).

        This action is irreversible. The document's embeddings will also be removed.

        Args:
            document_id: The document ID to delete.

        Raises:
            httpx.HTTPStatusError: If the deletion fails.
        """
        response = await self._client._client.delete(f"/documents/{document_id}")
        response.raise_for_status()

    # Phase 3: Chunks methods (async)

    async def list_chunks(self, document_id: int) -> ChunkList:
        """List all chunks for a specific document (async).

        Returns the text chunks that were created when the document was uploaded.

        Args:
            document_id: The document ID.

        Returns:
            ChunkList containing all chunks for the document.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        from albert_client.types import ChunkList

        response = await self._client._client.get(f"/chunks/{document_id}")
        response.raise_for_status()

        return ChunkList(**response.json())

    async def get_chunk(self, document_id: int, chunk_id: int) -> Chunk:
        """Get a specific chunk by document and chunk ID (async).

        Args:
            document_id: The document ID.
            chunk_id: The chunk ID.

        Returns:
            Chunk object with content and metadata.

        Raises:
            httpx.HTTPStatusError: If the chunk doesn't exist.
        """
        from albert_client.types import Chunk

        response = await self._client._client.get(f"/chunks/{document_id}/{chunk_id}")
        response.raise_for_status()

        return Chunk(**response.json())
