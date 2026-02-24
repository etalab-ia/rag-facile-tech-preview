"""RAG evaluation with Inspect AI.

Provides scorers, dataset adapters, and tasks for evaluating
rag-facile RAG pipelines using the Inspect AI framework.
"""

from rag_facile.evaluation._dataset import load_rag_dataset
from rag_facile.evaluation._scorers import (
    faithfulness,
    precision_at_k,
    rag_eval_scorer,
    recall_at_k,
)
from rag_facile.evaluation._tasks import rag_eval


__all__ = [
    "faithfulness",
    "load_rag_dataset",
    "precision_at_k",
    "rag_eval",
    "rag_eval_scorer",
    "recall_at_k",
]
