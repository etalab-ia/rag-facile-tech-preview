# memory

Flat-file persistent memory for the ragtime chat agent.

## Architecture

All state is stored as plain Markdown files under `.agent/`:

```
.agent/
├── MEMORY.md           # Semantic store — curated facts with fixed sections
├── profile.md          # User profile (language, experience, session count)
├── logs/
│   └── YYYY-MM-DD.md   # Episodic logs — append-only daily transcripts
└── sessions/
    └── *.md            # Session snapshots — archived full transcripts
```

## Agent Tools

The agent interacts with memory through three standard file-operation tools:

- `memory_read(path)` — list directories, read files with line numbers/ranges, auto-bootstrap `MEMORY.md`
- `memory_write(path, content)` — create or overwrite files, auto-create parent dirs
- `memory_edit(path, old, new)` — exact string replacement with uniqueness guard

All paths are relative to `.agent/` and protected against traversal (`..`, absolute paths).

## Dependencies

**Zero external dependencies** — stdlib only (`re`, `pathlib`, `glob`, `hashlib`).
