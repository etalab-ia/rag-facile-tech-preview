# rag-facile evaluation

RAG evaluation package using [Inspect AI](https://inspect.aisi.org.uk/) (UK AISI).

Provides three scorers for RAG pipeline evaluation:

- **recall@k** — fraction of relevant chunks actually retrieved
- **precision@k** — fraction of retrieved chunks that are relevant
- **faithfulness** — LLM-as-judge: is the answer grounded in context?

## Usage

```bash
# Run evaluation on a dataset
rag-facile eval data/datasets/golden_v1.jsonl

# Or use Inspect directly
inspect eval packages/evaluation/src/rag_facile/evaluation/_tasks.py \
  --model openai/openweight-medium
```
