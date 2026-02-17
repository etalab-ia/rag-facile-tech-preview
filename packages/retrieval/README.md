# Retrieval

Vector search for the RAG pipeline.

## Overview

This package provides search capabilities via the Albert API:

- **Semantic search**: Find chunks by meaning
- **Lexical search**: Find chunks by keywords
- **Hybrid search**: Combine semantic and lexical for best results

## Usage

```python
from rag_facile.retrieval import search_chunks

chunks = search_chunks(client, "energy transition", collection_ids=[1])
```

### Parameters

All parameters have sensible defaults from `ragfacile.toml`:

```python
chunks = search_chunks(
    client,
    "energy transition",
    collection_ids=[1],
    limit=10,             # Max results (default: config.retrieval.top_k)
    method="hybrid",      # "hybrid", "semantic", or "lexical"
    score_threshold=0.0,  # Minimum relevance score
)
```

## Configuration

```toml
[retrieval]
strategy = "hybrid"
top_k = 10
score_threshold = 0.0
```

## Related packages

- **[reranking](../reranking/)** — Re-score results with a cross-encoder
- **[context](../context/)** — Format chunks into LLM-ready context strings
- **[storage](../storage/)** — Collection management (create, delete, list, ingest)
- **[pipelines](../pipelines/)** — Orchestrates search → rerank → format

## Development

```bash
uv run pytest packages/retrieval/tests/
uv run ruff check packages/retrieval/
uv run ruff format packages/retrieval/
```
