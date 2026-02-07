"""Async Albert Client implementation."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from openai import AsyncOpenAI

if TYPE_CHECKING:
    from albert_client.types import RerankResponse, SearchResponse


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
