"""Inspect AI task definitions for rag-facile evaluation."""

from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.solver import generate

from rag_facile.evaluation._dataset import load_rag_dataset
from rag_facile.evaluation._scorers import (
    answer_correctness,
    faithfulness,
    precision_at_k,
    recall_at_k,
)
from rag_facile.evaluation._solvers import retrieve_rag_context


@task
def rag_eval(
    dataset_path: str = "data/datasets/golden_v1.jsonl",
    grader_model: str = "openai/openweight-medium",
) -> Task:
    """End-to-end evaluation of a rag-facile RAG pipeline.

    For each sample in the dataset:

    1. **Retrieve** — ``retrieve_rag_context`` calls ``AlbertPipeline.process_query``
       using the collections configured in ``ragfacile.toml`` and injects the
       retrieved passages into the prompt.
    2. **Generate** — the model answers the question given the retrieved context.
    3. **Score** — two LLM-as-judge metrics:
       - *faithfulness*: is the answer grounded in the retrieved context?
       - *answer_correctness*: does the answer match the reference answer?

    The dataset only needs ``user_input`` and ``reference`` fields — the
    ``retrieved_contexts`` from dataset generation are overwritten with live
    retrieval results.

    Args:
        dataset_path: Path to a rag-facile JSONL dataset.
        grader_model: Model identifier for both LLM-as-judge scorers.
    """
    return Task(
        dataset=load_rag_dataset(dataset_path),
        solver=[retrieve_rag_context(), generate()],
        scorer=[
            recall_at_k(),
            precision_at_k(),
            faithfulness(model=grader_model),
            answer_correctness(model=grader_model),
        ],
    )
