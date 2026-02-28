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
    - ``retrieved_contexts``: list of context passages captured during generation
      (used as ground-truth ``relevant_contexts`` for recall/precision scoring)
    - ``relevant_chunk_ids``: list of ground-truth relevant chunk IDs (optional)
    - ``retrieved_chunk_ids``: list of retrieved chunk IDs (optional)
    - ``_metadata``: optional extra metadata

    The loaded :class:`Sample` exposes two context metadata keys:

    - ``relevant_contexts``: the ground-truth passages from dataset generation
      (stable — never overwritten by solvers).
    - ``retrieved_contexts``: initialised to the same value but overwritten at
      eval time by :func:`retrieve_rag_context` with live pipeline results.

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

        # The JSONL's ``retrieved_contexts`` are the passages retrieved and
        # reranked *during dataset generation* — they are the ground-truth
        # passages used to write the reference answer.  We expose them under
        # two keys so the Inspect AI solver can overwrite ``retrieved_contexts``
        # with live pipeline results while ``relevant_contexts`` remains the
        # stable ground-truth for recall/precision scoring.
        ground_truth_contexts = row.get("retrieved_contexts", [])
        samples.append(
            Sample(
                input=row["user_input"],
                target=row.get("reference", ""),
                metadata={
                    "relevant_contexts": ground_truth_contexts,
                    "retrieved_contexts": ground_truth_contexts,
                    "relevant_chunk_ids": row.get("relevant_chunk_ids", []),
                    "retrieved_chunk_ids": row.get("retrieved_chunk_ids", []),
                    "source_file": meta.get("source_file", ""),
                    "retrieval_scores": meta.get("retrieval_scores", []),
                    "collection_ids": meta.get("collection_ids", []),
                },
            )
        )

    return MemoryDataset(samples=samples, name=path.stem)
