"""Custom Inspect AI solvers for rag-facile evaluation."""

from __future__ import annotations

import asyncio
import logging

import httpx
from inspect_ai.model import ChatMessageUser
from inspect_ai.solver import Solver, TaskState, solver


logger = logging.getLogger(__name__)


def _call_pipeline(question: str) -> tuple[str, list[str]]:
    """Call the RAG pipeline and return formatted context + individual chunk texts.

    Uses :meth:`~rag_facile.pipelines.RAGPipeline.retrieve_chunks` to fetch
    chunks in a single Albert API call, then formats them locally via
    :func:`~rag_facile.context.format_context`.  This avoids the double-search
    that would result from calling ``process_query`` (search + rerank + format)
    and then re-running the search separately to extract chunk texts.

    ``BasicPipeline.retrieve_chunks`` returns ``[]``, so pipelines without
    chunk-level retrieval produce an empty chunk list — retrieval metrics will
    be vacuously true, which is the correct behaviour (no chunks to measure).

    Returns:
        tuple of (formatted_context, list_of_chunk_texts)

        - formatted_context: citation-annotated string for injection into the
          LLM prompt (identical output to ``process_query``).
        - list_of_chunk_texts: individual passage texts stored in
          ``state.metadata["retrieved_contexts"]`` for the ``context_recall``
          and ``context_precision`` scorers.

    Extracted as a module-level helper so tests can patch it cleanly.
    """
    from rag_facile.context import format_context
    from rag_facile.core import get_config
    from rag_facile.pipelines import get_pipeline

    config = get_config()
    pipeline = get_pipeline(config)

    # Single Albert API call: search → optional rerank → chunks
    chunks = pipeline.retrieve_chunks(question)

    # Format context locally — same output as process_query, zero extra API calls
    context = format_context(chunks) if chunks else ""
    chunk_texts = [c.get("content", "") for c in chunks if c.get("content")]
    return context, chunk_texts


@solver
def retrieve_rag_context() -> Solver:
    """Run the RAG pipeline and inject retrieved context into the prompt.

    Calls :meth:`~rag_facile.pipelines.RAGPipeline.retrieve_chunks` using the
    collections configured in ``ragfacile.toml``.  The retrieved context is
    formatted and injected as a prefix to the user message.

    Two metadata keys are written for the scorers:

    - ``retrieved_contexts``: list[str] — individual chunk texts after
      search + rerank.  Used by ``context_recall`` and ``context_precision``
      (token-F1 comparison against ``relevant_contexts`` from the dataset).
    - The dataset's ``relevant_contexts`` are left untouched so scorers can
      compare retrieved vs relevant.

    If the pipeline returns no chunks (no collections configured, or no
    relevant chunks found), the dataset's pre-computed values are kept and the
    prompt is passed through unchanged.
    """

    async def solve(state: TaskState, generate: object) -> TaskState:  # noqa: ARG001
        question = state.input_text

        try:
            # retrieve_chunks is synchronous — run in a thread to avoid blocking
            # the Inspect AI event loop.
            loop = asyncio.get_running_loop()
            context, chunk_texts = await loop.run_in_executor(
                None, _call_pipeline, question
            )
        except (OSError, RuntimeError, ValueError, httpx.HTTPStatusError) as exc:
            # httpx.HTTPStatusError covers Albert API 4xx/5xx responses.
            # Retrieval failure is non-fatal: the solver falls back to the
            # pre-baked retrieved_contexts from the dataset.
            logger.warning("RAG pipeline retrieval failed: %s", exc)
            context = ""
            chunk_texts = []

        if context:
            # Overwrite with live retrieval results.
            # chunk_texts are individual passage texts for recall/precision scoring.
            state.metadata["retrieved_contexts"] = chunk_texts

        # NOTE: The RAG instruction below is intentionally in English.
        # TODO(i18n): Consider localising to French to match production chat apps,
        # where context injection uses French instructions. Raise with data scientists
        # before changing — it may affect score comparability across eval runs.
        #
        # NOTE(eval): format_context() adds citation markers ([1], source: file.pdf)
        # to the context injected here, which were absent during dataset generation.
        # This is a known minor inconsistency. Gather data scientist feedback before
        # deciding whether to strip citations for eval or align dataset generation.
        if context:
            augmented = (
                "Use the following context to answer the question. "
                "Only use information from the context. "
                "If the context does not contain the answer, say so.\n\n"
                f"## Context\n{context}\n\n"
                f"## Question\n{question}"
            )
        else:
            augmented = f"## Question\n{question}"
        state.messages = [
            ChatMessageUser(content=augmented),
            *state.messages[1:],
        ]
        return state

    return solve
