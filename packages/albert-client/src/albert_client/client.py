"""Main Albert Client implementation."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from openai import OpenAI

if TYPE_CHECKING:
    from albert_client.types import RerankResponse, SearchResponse


class AlbertClient:
    """Official Python SDK for France's Albert API.

    Provides OpenAI-compatible endpoints (chat, embeddings, audio, models) and
    Albert-specific endpoints (search, rerank, collections, documents, tools, management).

    Example:
        ```python
        from albert_client import AlbertClient

        # Initialize client
        client = AlbertClient(
            api_key="albert_...",  # Or set ALBERT_API_KEY env var
            base_url="https://albert.api.etalab.gouv.fr/v1"
        )

        # OpenAI-compatible endpoints
        response = client.chat.completions.create(
            model="AgentPublic/llama3-instruct-8b",
            messages=[{"role": "user", "content": "Hello!"}]
        )

        # Albert-specific endpoints (coming in Phase 2+)
        # results = client.search(prompt="...", collections=["..."])
        ```

    Architecture:
        - Wraps internal OpenAI client for OpenAI-compatible endpoints
        - Provides custom implementations for Albert-specific features
        - All responses use Pydantic models for type safety
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://albert.api.etalab.gouv.fr/v1",
        **kwargs,
    ):
        """Initialize Albert client.

        Args:
            api_key: Albert API key. If not provided, reads from ALBERT_API_KEY env var.
            base_url: Base URL for Albert API (includes /v1 suffix).
            **kwargs: Additional arguments passed to OpenAI client (timeout, max_retries, etc.).
        """
        # Get API key from env if not provided
        if api_key is None:
            api_key = os.environ.get("ALBERT_API_KEY")

        if not api_key:
            raise ValueError(
                "Albert API key is required. Provide via api_key parameter or "
                "ALBERT_API_KEY environment variable."
            )

        # Initialize wrapped OpenAI client
        self._client = OpenAI(api_key=api_key, base_url=base_url, **kwargs)

        # OpenAI-Compatible Passthrough (direct proxy to internal client)
        self.chat = self._client.chat
        self.embeddings = self._client.embeddings
        self.audio = self._client.audio
        self.models = self._client.models

        # Albert-Specific Resources (will be implemented in Phase 2+)
        # self.collections = Collections(self._client)
        # self.documents = Documents(self._client)
        # self.tools = Tools(self._client)
        # self.management = Management(self._client)

    @property
    def api_key(self) -> str:
        """Get the API key."""
        return self._client.api_key

    @property
    def base_url(self) -> str:
        """Get the base URL."""
        return str(self._client.base_url)

    # Phase 2: Search and Rerank methods

    def search(
        self,
        prompt: str,
        collections: list[str | int] | None = None,
        limit: int = 10,
        offset: int = 0,
        method: str = "semantic",
        score_threshold: float | None = None,
        rff_k: int = 20,
    ) -> SearchResponse:
        """Hybrid RAG search across collections.

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
            results = client.search(
                prompt="Loi Énergie Climat",
                collections=["col_123"],
                limit=5,
                method="hybrid"
            )
            for result in results.data:
                print(f"Score: {result.score:.3f}")
                print(f"Content: {result.chunk.content[:100]}...")
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
        response = self._client._client.post("/search", json=body)
        response.raise_for_status()

        # Parse and return Pydantic model
        return SearchResponse(**response.json())

    def rerank(
        self,
        query: str,
        documents: list[str],
        model: str,
        top_n: int | None = None,
    ) -> RerankResponse:
        """Rerank documents by relevance to a query using BGE reranker.

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
            results = client.rerank(
                query="transition énergétique",
                documents=[
                    "La loi Énergie Climat vise à...",
                    "Le changement climatique est...",
                    "Les énergies renouvelables..."
                ],
                model="BAAI/bge-reranker-v2-m3",
                top_n=2
            )
            for result in results.results:
                print(f"Rank {result.index}: Score {result.relevance_score:.3f}")
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
        response = self._client._client.post("/rerank", json=body)
        response.raise_for_status()

        # Parse and return Pydantic model
        return RerankResponse(**response.json())
