"""Load rag-facile JSONL datasets into Inspect AI format."""

from __future__ import annotations

import json
from pathlib import Path

from inspect_ai.dataset import MemoryDataset, Sample


def load_rag_dataset(path: str | Path) -> MemoryDataset:
    """Load a rag-facile JSONL dataset into an Inspect AI Dataset.

    Each line in the JSONL file should contain:
    - ``user_input``: the question
    - ``reference``: the ground truth answer
    - ``retrieved_contexts``: list of context passages (text)
    - ``relevant_chunk_ids``: list of ground-truth relevant chunk IDs
    - ``retrieved_chunk_ids``: list of actually retrieved chunk IDs
    - ``_metadata``: optional extra metadata

    Args:
        path: Path to a ``.jsonl`` file produced by ``rag-facile generate-dataset``.

    Returns:
        An Inspect AI :class:`MemoryDataset` ready for use in a :class:`Task`.
    """
    path = Path(path)
    samples: list[Sample] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        meta = row.get("_metadata", {})

        samples.append(
            Sample(
                input=row["user_input"],
                target=row.get("reference", ""),
                metadata={
                    "retrieved_contexts": row.get("retrieved_contexts", []),
                    "relevant_chunk_ids": row.get("relevant_chunk_ids", []),
                    "retrieved_chunk_ids": row.get("retrieved_chunk_ids", []),
                    "source_file": meta.get("source_file", ""),
                    "retrieval_scores": meta.get("retrieval_scores", []),
                    "collection_ids": meta.get("collection_ids", []),
                },
            )
        )

    return MemoryDataset(samples=samples, name=path.stem)
