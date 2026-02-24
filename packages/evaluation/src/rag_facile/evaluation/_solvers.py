"""Custom Inspect AI solvers for rag-facile evaluation."""

from __future__ import annotations

import asyncio
import logging

from inspect_ai.model import ChatMessageUser
from inspect_ai.solver import Solver, TaskState, solver


logger = logging.getLogger(__name__)


def _call_pipeline(question: str) -> str:
    """Call the RAG pipeline and return the formatted context string.

    Extracted as a module-level helper so tests can patch it cleanly.
    """
    from rag_facile.core import get_config
    from rag_facile.pipelines import get_pipeline

    config = get_config()
    pipeline = get_pipeline(config)
    return pipeline.process_query(question)


@solver
def retrieve_rag_context() -> Solver:
    """Run the RAG pipeline and inject retrieved context into the prompt.

    Calls ``AlbertPipeline.process_query()`` using the collections configured
    in ``ragfacile.toml``.  The retrieved context is injected as a prefix to
    the user message and stored in ``state.metadata["retrieved_contexts"]``
    for the faithfulness scorer.

    If the pipeline returns no context (no collections configured, or no
    relevant chunks found), the prompt is passed through unchanged and
    faithfulness is skipped (vacuously true).
    """

    async def solve(state: TaskState, generate: object) -> TaskState:  # noqa: ARG001
        question = state.input_text

        try:
            # process_query is synchronous — run in a thread to avoid blocking
            # the Inspect AI event loop.
            loop = asyncio.get_event_loop()
            context: str = await loop.run_in_executor(None, _call_pipeline, question)
        except Exception:
            logger.warning("RAG pipeline retrieval failed", exc_info=True)
            context = ""

        if not context:
            return state

        # Overwrite any pre-computed contexts from the dataset with the
        # freshly retrieved ones so the faithfulness scorer uses live results.
        state.metadata["retrieved_contexts"] = [context]

        augmented = (
            "Use the following context to answer the question. "
            "Only use information from the context. "
            "If the context does not contain the answer, say so.\n\n"
            f"## Context\n{context}\n\n"
            f"## Question\n{question}"
        )
        state.messages = [
            ChatMessageUser(content=augmented),
            *state.messages[1:],
        ]
        return state

    return solve
