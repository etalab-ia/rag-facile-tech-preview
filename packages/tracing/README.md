# ragtime-tracing

RAG pipeline tracing — log queries, retrieved context, LLM responses, and user feedback.

Part of the [ragtime](https://github.com/etalab-ia/ragtime) project.

## Built-in providers

- **SQLite** (default) — zero-dependency, file-based, uses WAL mode for concurrent access
- **Noop** — discards all data (when tracing is disabled)

## Configuration

```toml
[tracing]
enabled = true
provider = "sqlite"
database = ".ragtime/traces.db"
```
