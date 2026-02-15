# Retrieval

Search, reranking, and context formatting for the RAG pipeline.

## Overview

This package provides retrieval capabilities:

- **Search**: Find relevant document chunks via Albert API (semantic, lexical, or hybrid)
- **Reranking**: Re-score results with a cross-encoder for higher precision
- **Context formatting**: Convert retrieved chunks into LLM-ready context strings with citations

## Usage

```python
from retrieval import retrieve, format_context

# Search + optional rerank (config-driven)
chunks = retrieve(client, "What is RAG?", collection_ids=[1])

# Format for LLM injection
context = format_context(chunks)
```

### Convenience function

```python
from retrieval import process_query

# Search + rerank + format in one call
context = process_query("What is RAG?", collection_ids=[1])
```

## Configuration

Parameters default to `ragfacile.toml` values:

```toml
[retrieval]
strategy = "hybrid"     # "hybrid", "semantic", or "lexical"
top_k = 10
score_threshold = 0.0

[reranking]
enabled = true
model = "openweight-rerank"
top_n = 3

[formatting.citations]
enabled = true
style = "inline"        # "inline" or "footnote"
```

## Related packages

- **[storage](../storage/)** — Collection management (create, delete, list, ingest documents)
- **[ingestion](../ingestion/)** — Document text extraction (PDF, Markdown, HTML)
- **[pipelines](../pipelines/)** — Pipeline orchestration (coordinates ingestion, storage, and retrieval)

## Development

```bash
uv run pytest packages/retrieval/tests/
uv run ruff check packages/retrieval/
uv run ruff format packages/retrieval/
```
