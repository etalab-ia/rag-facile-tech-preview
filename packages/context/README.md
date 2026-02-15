# Context

Context assembly for RAG pipelines - format retrieved chunks into LLM-ready context strings.

## Overview

The `context` package provides utilities to convert retrieved document chunks into formatted context strings suitable for injection into LLM prompts. It supports:

- Inline and footnote citation styles
- Optional source attribution (file, page number)
- Configurable formatting via `rag-core` config

## Installation

This package is part of the RAG pipeline workspace:

```bash
uv pip install -e packages/context
```

## Usage

```python
from context import format_context
from rag_core import RetrievedChunk

# Format retrieved chunks with inline citations
chunks = [
    RetrievedChunk(
        content="La loi Energie Climat vise a...",
        score=0.92,
        source_file="rapport.pdf",
        page=5,
        collection_id=1,
        document_id=1,
        chunk_id=1,
    ),
    RetrievedChunk(
        content="Les energies renouvelables...",
        score=0.88,
        source_file="guide.pdf",
        page=12,
        collection_id=1,
        document_id=2,
        chunk_id=3,
    ),
]

context_str = format_context(chunks, include_citations=True)
print(context_str)
```

**Output:**
```
--- Retrieved context ---
[1] La loi Energie Climat vise a... (source: rapport.pdf, p.5)

[2] Les energies renouvelables... (source: guide.pdf, p.12)
--- End of context ---
```

### Citation Styles

```python
# Inline citations (default)
context_str = format_context(chunks, citation_style="inline")
# [1] Content here (source: doc.pdf, p.5)

# Footnote citations
context_str = format_context(chunks, citation_style="footnote")
# Content here [1]

# No citations
context_str = format_context(chunks, include_citations=False)
# Content here
```

## Configuration

Citation settings are inherited from `rag-core` config:

```python
from rag_core import get_config

config = get_config()
config.formatting.citations.enabled = True
config.formatting.citations.style = "inline"  # or "footnote"
```

## Dependencies

- **rag-core**: Core types and configuration (workspace dependency)

## Related Packages

- **retrieval**: Vector search and chunk retrieval
- **reranking**: Re-rank retrieved chunks
- **pipelines**: End-to-end RAG orchestration
