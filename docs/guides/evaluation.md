# Evaluating Your RAG Application

Before deploying, you need to know if your RAG application works well. Evaluation answers three key questions: Is my chatbot giving correct answers? Does it find the right documents? Is it hallucinating?

## Generate Synthetic Evaluation Datasets

Don't have evaluation data? Generate it automatically from your documents using the **Data Foundry** feature. Choose between Letta Cloud or self-hosted Albert API.

### Option 1: Letta Cloud (Easiest)

```bash
# Set up Letta Cloud credentials
export LETTA_API_KEY="your-letta-api-key"           # Get at https://app.letta.com/api-keys
export DATA_FOUNDRY_AGENT_ID="agent-xxx"            # Pre-configured agent ID

# Generate Q/A pairs from your documents
rag-facile generate-dataset ./my-docs -o golden_dataset.jsonl -n 50 --provider letta
```

### Option 2: Albert API (Self-Hosted)

```bash
# Set up Albert API credentials
export OPENAI_API_KEY="your-api-key"                # Albert API key
export OPENAI_BASE_URL="http://localhost:8000"      # Albert API endpoint
export OPENAI_MODEL="mistral-7b"                    # Model to use

# Generate Q/A pairs using your Albert instance
rag-facile generate-dataset ./my-docs -o golden_dataset.jsonl -n 50 --provider albert
```

### Output Format

Both providers create [Ragas](https://docs.ragas.io/)-compatible JSONL files with French Q/A pairs:

```json
{
  "user_input": "Quel est le délai de recours administratif?",
  "retrieved_contexts": ["Le délai de recours est de deux mois..."],
  "reference": "Le délai de recours administratif est de deux mois.",
  "_metadata": {"source_file": "code.pdf", "quality_score": 0.95}
}
```

## Basic Evaluation Workflow

```python
from datasets import load_dataset

# Load a dataset from HuggingFace
dataset = load_dataset("AgentPublic/service-public")

# Run your RAG pipeline on each question
results = []
for example in dataset["train"]:
    answer = your_rag_pipeline(example["question"])
    results.append({
        "question": example["question"],
        "expected": example["ground_truth"],
        "actual": answer,
    })

# Measure accuracy
accuracy = sum(1 for r in results if r["expected"] == r["actual"]) / len(results) if results else 0.0
```

## What to Measure

| Metric | What it Measures |
|--------|------------------|
| **Accuracy** | Correct answers / Total questions |
| **Retrieval Recall** | Did we find the right documents? |
| **Faithfulness** | Does the answer match the sources? |
| **Latency** | Response time |

For sovereign AI, also consider: sovereignty (only *.gouv.fr sources), energy score, and French language quality.

## Further Reading

- [Ragas Documentation](https://docs.ragas.io/) — The framework used for RAG evaluation metrics
- [Letta Evals](https://github.com/letta-ai/letta-evals) — Framework for testing AI agents
- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) — Embedding model benchmarks
- [BEIR Benchmark](https://github.com/beir-cellar/beir) — Information retrieval benchmarks
