# Evaluating Your RAG Application

Before deploying, you need to know if your RAG application works well. Evaluation answers three key questions: Is my chatbot giving correct answers? Does it find the right documents? Is it hallucinating?

## Evaluation Assets

All evaluation data lives in the `data/` directory at your workspace root:

```
data/
├── documents/         # Reference documents for dataset generation
│   ├── raw/           # Original PDFs, markdown, HTML files
│   └── processed/     # Chunked/parsed output (auto-generated)
├── datasets/          # Q/A datasets (generated or pulled from HF)
│   └── golden_v1.jsonl
├── traces/            # Exported pipeline traces
└── evals/             # Inspect AI evaluation logs
    └── logs/
```

- `data/documents/` and `data/datasets/` are **git-tracked** (small files, reproducibility matters)
- `data/traces/` and `data/evals/` are **gitignored** (large, regenerable)

## Step 1: Generate a Dataset

Place your reference documents in `data/documents/raw/`, then generate Q/A pairs:

### Option 1: Letta Cloud (Easiest)

```bash
export LETTA_API_KEY="your-letta-api-key"
export DATA_FOUNDRY_AGENT_ID="agent-xxx"

rag-facile generate-dataset data/documents/raw/ -o data/datasets/golden_v1.jsonl -n 50 --provider letta
```

### Option 2: Albert API (Self-Hosted)

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="http://localhost:8000"
export OPENAI_MODEL="openweight-small"

rag-facile generate-dataset data/documents/raw/ -o data/datasets/golden_v1.jsonl -n 50 --provider albert
```

### Dataset Format

Both providers create JSONL files with French Q/A pairs:

```json
{
  "user_input": "Quel est le délai de recours administratif?",
  "retrieved_contexts": ["Le délai de recours est de deux mois..."],
  "reference": "Le délai de recours administratif est de deux mois.",
  "relevant_chunk_ids": ["chunk-abc123"],
  "retrieved_chunk_ids": ["chunk-abc123", "chunk-def456"],
  "_metadata": {"source_file": "code.pdf", "quality_score": 0.95}
}
```

## Step 2: Run Evaluation

rag-facile uses [Inspect AI](https://inspect.aisi.org.uk/) (UK AI Security Institute) to run evaluations. Three metrics are computed:

| Metric | What it Measures |
|--------|-----------------|
| **Recall@k** | Of the relevant chunks, how many were retrieved? |
| **Precision@k** | Of the retrieved chunks, how many were relevant? |
| **Faithfulness** | Is the answer grounded in the context? (LLM-as-judge) |

Run an evaluation:

```bash
rag-facile eval run data/datasets/golden_v1.jsonl
```

Or use the latest dataset automatically:

```bash
rag-facile eval run
```

Options:
- `--model` — Model for generation and faithfulness scoring (default: `openai/openweight-medium`)
- `--log-dir` — Override where Inspect logs are stored

## Step 3: View Results

Open the Inspect AI web viewer:

```bash
rag-facile eval view
```

Or list past runs:

```bash
rag-facile eval list
```

## Advanced: Using Inspect AI Directly

The evaluation package exposes standard Inspect AI tasks. You can run them directly:

```bash
inspect eval packages/evaluation/src/rag_facile/evaluation/_tasks.py \
  --model openai/openweight-medium \
  -T dataset_path=data/datasets/golden_v1.jsonl
```

### Custom Scorers

You can use individual scorers in your own Inspect tasks:

```python
from rag_facile.evaluation import recall_at_k, precision_at_k, faithfulness

# Use as standalone scorers
scorer = recall_at_k()

# Or the combined multi-scorer
from rag_facile.evaluation import rag_eval_scorer
scorer = rag_eval_scorer(model="openai/openweight-medium")
```

## Configuration

Evaluation settings in `ragfacile.toml`:

```toml
[eval]
provider = "albert"              # Dataset generation provider
target_samples = 50              # Number of Q/A pairs to generate
output_format = "jsonl"          # Output format
data_dir = "data"                # Root for evaluation assets
inspect_log_dir = "data/evals/logs"  # Inspect AI log directory
```

## What to Measure Beyond Metrics

For sovereign AI, also consider: sovereignty (only *.gouv.fr sources), energy score, and French language quality.

## Further Reading

- [Inspect AI Documentation](https://inspect.aisi.org.uk/) — The evaluation framework
- [Ragas Documentation](https://docs.ragas.io/) — RAG evaluation metrics reference
- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) — Embedding model benchmarks
