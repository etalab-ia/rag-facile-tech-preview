"""Inspect AI task definitions for rag-facile evaluation."""

from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.solver import generate

from rag_facile.evaluation._dataset import load_rag_dataset
from rag_facile.evaluation._scorers import rag_eval_scorer
from rag_facile.evaluation._solvers import inject_rag_context


@task
def rag_eval(
    dataset_path: str = "data/datasets/golden_v1.jsonl",
    grader_model: str = "openai/openweight-medium",
) -> Task:
    """Evaluate a rag-facile RAG pipeline.

    Loads a JSONL dataset, injects pre-computed context into each prompt,
    generates answers, and scores them on recall@k, precision@k, and
    faithfulness.

    Args:
        dataset_path: Path to a rag-facile JSONL dataset.
        grader_model: Model for the faithfulness LLM-as-judge scorer.
    """
    return Task(
        dataset=load_rag_dataset(dataset_path),
        solver=[inject_rag_context(), generate()],
        scorer=rag_eval_scorer(model=grader_model),
    )
