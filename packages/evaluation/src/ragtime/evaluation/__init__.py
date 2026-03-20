"""RAG evaluation with Inspect AI.

Provides scorers, dataset adapters, solvers, and tasks for evaluating
ragtime RAG pipelines using the Inspect AI framework.
"""

from ragtime.evaluation._dataset import load_rag_dataset
from ragtime.evaluation._scorers import (
    answer_correctness,
    context_precision,
    context_recall,
    faithfulness,
    rag_eval_scorer,
)
from ragtime.evaluation._solvers import retrieve_rag_context
from ragtime.evaluation._tasks import rag_eval


__all__ = [
    "answer_correctness",
    "context_precision",
    "context_recall",
    "faithfulness",
    "load_rag_dataset",
    "rag_eval",
    "rag_eval_scorer",
    "retrieve_rag_context",
]
