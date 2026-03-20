# ragtime-lib

Python library for building RAG (Retrieval-Augmented Generation) applications, designed for the French government ecosystem.

## Installation

```bash
uv add ragtime-lib
```

## Usage

```python
from ragtime.core import get_config
from ragtime.pipelines import process_file, process_query
from albert import AsyncAlbertClient
```

## Packages included

- `ragtime.core` — Configuration, schema, presets
- `ragtime.pipelines` — RAG pipeline orchestration
- `ragtime.ingestion` — Document parsing (PDF, Markdown, HTML)
- `ragtime.retrieval` — Vector search
- `ragtime.reranking` — Cross-encoder re-scoring
- `ragtime.context` — Context formatting for LLM prompts
- `ragtime.storage` — Collection management

The `albert-client` package (Albert API SDK) is installed as a separate dependency.
