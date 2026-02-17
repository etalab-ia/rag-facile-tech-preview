# Reranking

Re-score retrieved chunks with a cross-encoder for higher precision in RAG pipelines.

## Overview

The `reranking` package provides reranking capabilities that improve the quality of retrieved chunks by re-scoring them using cross-encoder models. Unlike bi-encoder models used in vector search (which encode queries and documents separately), cross-encoders process query-document pairs together, resulting in more accurate relevance scores.

## Installation

This package is part of a workspace. Install it with:

```bash
uv pip install -e packages/reranking
```

## Usage

```python
from albert import AlbertClient
from rag_facile.reranking import rerank_chunks
from rag_facile.core import RetrievedChunk

# Initialize client
client = AlbertClient(api_key="your-api-key")

# Assume you have chunks from retrieval
chunks: list[RetrievedChunk] = [...]

# Rerank chunks by relevance to query
reranked = rerank_chunks(
    client,
    query="What is retrieval-augmented generation?",
    chunks=chunks,
    model="openweight-rerank",  # optional, default model
    top_n=5,  # optional, return only top 5
)

# Use the reranked chunks (ordered by relevance)
for chunk in reranked:
    print(f"Score: {chunk['score']:.3f} - {chunk['content'][:100]}...")
```

## API Reference

### `rerank_chunks`

```python
def rerank_chunks(
    client: AlbertClient,
    query: str,
    chunks: list[RetrievedChunk],
    *,
    model: str = "openweight-rerank",
    top_n: int | None = None,
) -> list[RetrievedChunk]
```

**Parameters:**
- `client`: Authenticated Albert client
- `query`: The query to rank chunks against
- `chunks`: List of retrieved chunks to rerank
- `model`: Reranker model name (default: "openweight-rerank")
- `top_n`: Return only top N results. If None, returns all chunks

**Returns:**
- List of reranked chunks, ordered by relevance (highest first)

## Pipeline Integration

The reranking package is typically used as a middle stage in the RAG pipeline:

1. **Retrieval** (`retrieval` package) - Get initial candidates via vector search
2. **Reranking** (this package) - Re-score candidates for precision
3. **Context Formatting** (`context` package) - Format selected chunks for LLM

```python
# Example pipeline
from rag_facile.retrieval import search_chunks
from rag_facile.reranking import rerank_chunks
from rag_facile.context import format_context

# 1. Retrieve candidates
chunks = search_chunks(client, query, collection_id=1, top_k=20)

# 2. Rerank for precision
reranked = rerank_chunks(client, query, chunks, top_n=5)

# 3. Format for LLM
context = format_context(reranked)
```

## License

See the workspace root for license information.
