# rag-core

Configuration management and shared types for the Ragtime pipeline.

## Overview

The `rag-core` package provides:

- **`RAGConfig`** — Pydantic model covering all 12 RAG pipeline stages
- **`load_config` / `get_config`** — Load from `ragtime.toml`, with env var overrides
- **`load_preset` / `list_presets`** — Battle-tested preset configurations
- **`RetrievedChunk`** — Shared TypedDict used across retrieval, reranking, and context modules
- **`PIPELINE_STAGES`** — Ordered metadata for all pipeline stages (used by `ragtime config show`)

## Installation

This package is bundled into `ragtime-lib`. To use it standalone in the workspace:

```bash
uv pip install -e packages/rag-core
```

## Usage

### Load configuration

```python
from ragtime.core import load_config, get_config

# Load from ragtime.toml (auto-searches parent dirs)
config = load_config()

# Singleton pattern (cached after first load)
config = get_config()

print(config.generation.model)   # "openweight-medium"
print(config.retrieval.top_k)    # 10
```

### Use a preset

```python
from ragtime.core.presets import load_preset, list_presets

print(list_presets())  # ['accurate', 'balanced', 'fast', 'hr', 'legal']

config = load_preset("legal")
print(config.hallucination.enabled)  # True
```

### Environment variable overrides

```bash
# Any config value can be overridden at runtime
export RAG_GENERATION_MODEL="openweight-large"
export RAG_RETRIEVAL_TOP_K="20"
export RAG_RERANKING_ENABLED="false"
```

### Shared types

```python
from ragtime.core import RetrievedChunk

chunks: list[RetrievedChunk] = [
    RetrievedChunk(
        content="La loi Energie Climat vise à...",
        score=0.92,
        source_file="rapport.pdf",
        page=5,
        collection_id=1,
        document_id=1,
        chunk_id=1,
    )
]
```

## Presets

| Preset | Philosophy |
|--------|-----------|
| **balanced** | Quality/speed tradeoff (recommended default) |
| **fast** | Speed-optimized: smaller model, no reranking |
| **accurate** | Quality-optimized: larger model, hallucination detection |
| **legal** | Strict citations, low temperature, accuracy validation |
| **hr** | Privacy-aware, clear attribution, semantic search |

## Configuration sections

12 pipeline stages, each tunable in `ragtime.toml`:

`eval` · `ingestion` · `chunking` · `embedding` · `storage` · `query` ·
`retrieval` · `reranking` · `context` · `generation` · `hallucination` · `formatting`

See [`ragtime.toml` Reference](../../docs/reference/ragfacile-toml.md) for full documentation.

## Related packages

- **ragtime-lib**: Bundles this package with all other pipeline modules for distribution
- **pipelines**: Orchestrates the full RAG pipeline using this config
