# Components Reference

RAG Facile ships with ready-to-use components: an Albert API client, two frontend applications, and pluggable modules.

## Albert Client SDK

Official Python SDK for the [Albert API](https://albert.sites.beta.gouv.fr/). OpenAI-compatible with features specific to French government administration.

**Installation:**

```bash
pip install albert-client
```

**Usage Example:**

```python
from albert_client import AlbertClient

client = AlbertClient(
    api_key="your-api-key",
    base_url="https://albert.api.etalab.gouv.fr/v1"
)

# OpenAI-compatible
response = client.chat.completions.create(
    model="openweight-small",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Hybrid search with reranking
results = client.search(
    query="energy transition",
    collections=[1, 2],
    method="hybrid"
)
```

**Full Documentation:** [Albert Client SDK README](../../packages/albert-client/README.md)

## Frontend Applications

| App | Description | Default Port |
|-----|-------------|--------------|
| **Chainlit Chat** | Chat interface with file upload support | 8000 |
| **Reflex Chat** | Interactive chat with modern UI | 3000 |

Both are available during `rag-facile setup` and are pre-configured to work with the Albert API out of the box.

## Retrieval Modules

RAG Facile provides two pluggable retrieval modules. Choose one during setup based on your needs.

### PDF (retrieval-basic)

**Best for:** Quick prototypes, offline usage, simple document processing

- **Extraction:** Local pypdf library (no network calls)
- **Fallback:** Automatic fallback from Albert API if parsing fails
- **Supported formats:** PDF
- **Features:** Simple, lightweight, no server dependencies
- **Use case:** Getting started quickly, private/offline scenarios

### Albert RAG (retrieval-albert)

**Best for:** Production deployments, multiple file formats, advanced search features

- **Extraction:** Albert API server-side parsing (`/parse-beta`)
- **Supported formats:** PDF, JSON, Markdown, HTML
- **Features:** 
  - Multi-format document support
  - Server-side chunking and vectorization
  - Hybrid search (semantic + lexical)
  - Result reranking
  - Built-in fallback to local pypdf if parse API fails
- **Use case:** Advanced RAG pipelines, production applications

> **Note:** Future releases will add collection-based search and RAG sessions to the Reflex and Chainlit apps when using Albert RAG. Currently, both modules extract text and inject it as context inline.

Modules are selected during `rag-facile setup` and automatically included in your project.
