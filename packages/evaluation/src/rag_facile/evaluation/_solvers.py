"""Custom Inspect AI solvers for rag-facile evaluation."""

from __future__ import annotations

import asyncio
import logging

from inspect_ai.model import ChatMessageUser
from inspect_ai.solver import Solver, TaskState, solver


logger = logging.getLogger(__name__)


def _call_pipeline(question: str) -> tuple[str, list[int]]:
    """Call the RAG pipeline and return formatted context + chunk IDs.

    Returns:
        tuple of (formatted_context, list_of_chunk_ids_retrieved)

    Extracted as a module-level helper so tests can patch it cleanly.
    """
    from rag_facile.core import get_config
    from rag_facile.pipelines import get_pipeline
    from rag_facile.retrieval import search_chunks

    config = get_config()
    pipeline = get_pipeline(config)

    # Get the formatted context from the pipeline
    context = pipeline.process_query(question)

    # Extract chunk IDs from a fresh search using the same config
    # The pipeline internally calls search_chunks, but we recreate that call
    # to capture the chunk IDs directly (they're not exposed by process_query).
    try:
        # Get collections: explicit, session, or from config
        collection_ids = config.storage.collections
        if pipeline._collection_id:
            collection_ids = list(set(collection_ids) | {pipeline._collection_id})

        if collection_ids:
            client = pipeline.client
            chunks = search_chunks(
                client,
                question,
                collection_ids,
                limit=config.retrieval.top_k,
                method=config.retrieval.strategy,
                score_threshold=config.retrieval.score_threshold,
            )
            chunk_ids = [
                chunk.get("chunk_id", 0) for chunk in chunks if chunk.get("chunk_id")
            ]
            return context, chunk_ids
    except Exception:
        logger.warning("Failed to extract chunk IDs from search", exc_info=True)

    return context, []


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
            context, chunk_ids = await loop.run_in_executor(
                None, _call_pipeline, question
            )
        except Exception:
            logger.warning("RAG pipeline retrieval failed", exc_info=True)
            context = ""
            chunk_ids = []

        if not context:
            return state

        # Overwrite any pre-computed contexts from the dataset with the
        # freshly retrieved ones so the faithfulness scorer uses live results.
        state.metadata["retrieved_contexts"] = [context]
        # Store chunk IDs for precision@k and recall@k scorers
        state.metadata["retrieved_chunk_ids"] = [str(cid) for cid in chunk_ids]

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
