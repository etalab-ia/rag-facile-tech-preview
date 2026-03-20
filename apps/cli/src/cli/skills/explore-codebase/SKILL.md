---
name: explore-codebase
description: Navigate the ragtime source code — find where things are implemented.
triggers: ["source", "code", "where is", "où est", "how is implemented", "comment est implémenté", "package", "module", "fichier", "file"]
---

# Skill: Explore Codebase

You are helping the user understand the ragtime source structure. Use the available
tools to give accurate, specific answers rather than guessing.

## Navigation strategy

1. Call `get_agents_md()` first — AGENTS.md has the package tree and key file locations
2. Call `get_recent_git_activity()` for "what changed recently?" questions
3. Call `run_ragtime("config show --format json")` to cross-reference config with implementation

## Package map (ragtime namespace)

| Package | Import | Responsibility |
|---------|--------|---------------|
| `rag-core` | `ragtime.core` | Config schema, shared types, presets |
| `ingestion` | `ragtime.ingestion` | PDF/MD/HTML parsing → Albert upload |
| `storage` | `ragtime.storage` | Albert collection management |
| `retrieval` | `ragtime.retrieval` | Vector search → RetrievedChunk list |
| `reranking` | `ragtime.reranking` | Cross-encoder re-scoring |
| `context` | `ragtime.context` | Format chunks → LLM prompt string |
| `pipelines` | `ragtime.pipelines` | Orchestrates all phases end-to-end |
| `query` | `ragtime.query` | Multi-query / HyDE expansion |
| `albert-client` | `albert` | Albert API SDK (versioned independently) |

## Apps

| App | Entry point | Purpose |
|-----|------------|---------|
| `apps/cli` | `ragtime` | Main CLI + chat harness |
| `apps/chainlit-chat` | `just run` | Chainlit web UI |
| `apps/reflex-chat` | `just run reflex` | Reflex web UI |

## When asked "where is X configured?"
Always cite the exact ragtime.toml section and the Pydantic model that validates it
(found in `packages/rag-core/src/ragtime/core/schema.py`).
