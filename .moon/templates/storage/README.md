# Storage

Vector storage and collection management for the RAG pipeline.

## Providers

| Provider | Backend | Config value |
|----------|---------|--------------|
| **Albert** | Albert API collections | `albert-collections` |
| **Local** | SQLite (planned) | `local-sqlite` |

## Usage

```python
from storage import get_provider

# Backend determined by ragfacile.toml [storage] section
provider = get_provider()

# Collection lifecycle
collection_id = provider.create_collection(client, "my-docs", "Project documents")
doc_ids = provider.ingest_documents(client, ["report.pdf", "guide.md"], collection_id)
collections = provider.list_collections(client)
provider.delete_collection(client, collection_id)
```

## Configuration

```toml
# ragfacile.toml
[storage]
provider = "albert-collections"  # or "local-sqlite" (planned)
collection_naming = "workspace"
distance_metric = "cosine"
```
