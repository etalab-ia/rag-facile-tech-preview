---
name: rag-cli
description: Run any ragtime CLI command on behalf of the user. Use when the user wants to list collections, inspect config, generate an evaluation dataset, or run any other ragtime operation.
triggers: ["collections", "generate-dataset", "dataset", "version", "commandes"]
---

# Skill: rag-cli

You can run any ragtime CLI command using the `run_ragtime` tool.
This is more powerful than explaining commands — you actually execute them and
show the user the real output.

## Available commands

### Read-only (run freely, no confirmation needed)

| Command | What it does |
|---|---|
| `version` | Show installed ragtime version |
| `config show` | Display the current ragtime.toml configuration |
| `collections list` | List all accessible Albert API collections |
| `collections list --limit 20` | Limit results to 20 collections |

### Write operations (ALWAYS confirm before running)

| Command | What it does |
|---|---|
| `generate-dataset ./docs -o golden_dataset.jsonl -n 20 --provider albert` | Generate synthetic Q&A evaluation dataset |

## How to use run_ragtime

Call `run_ragtime(subcommand)` where subcommand is everything after `ragtime`:

```
run_ragtime("collections list")
run_ragtime("config show")
run_ragtime("generate-dataset ./docs -o golden.jsonl -n 20 --provider albert")
```

## Updating config values

Use `run_ragtime("config set <key> <value>")` for config changes. The CLI validates
the key against the Pydantic schema, shows old → new value, and saves the file.

Examples:
```
run_ragtime("config set storage.collections [783, 785, 79783]")
run_ragtime("config set retrieval.top_k 15")
run_ragtime("config set generation.model openweight-large")
```

ALWAYS confirm with the user before running config set — explain the tradeoff first.

## Generate-dataset workflow

1. Ask the user for the docs directory path
2. Suggest `golden_dataset.jsonl` as the output file
3. Recommend 20 questions for a first run (duration depends on document size and API latency)
4. Confirm: "Je vais lancer : ragtime generate-dataset <path> -o <file> -n <n> --provider albert. Cela prendra environ X minutes. Puis-je démarrer ?"
5. On yes: call `run_ragtime("generate-dataset <path> -o <file> -n <n> --provider albert")`
6. Explain next steps: use `ragtime eval --dataset <file>` to measure pipeline quality

## Collections workflow

1. Call `run_ragtime("collections list")` to show available collections
2. Explain public vs private collections
3. Call `run_ragtime("config show --format json")` to read the current config (includes `storage.collections`)
4. Compute the new list by adding or removing the requested ID(s)
5. After user confirmation, call `run_ragtime("config set storage.collections [id1, id2, ...]")`

## Rules

- Read-only commands: run immediately, no confirmation needed
- Write operations: ALWAYS confirm with the user first
- Config changes: use run_ragtime("config set ...") — always confirm first
- Never construct shell commands outside the allowed subcommands
- If output is long, summarise the key points rather than dumping everything
