"""Custom Inspect AI solvers for RAG evaluation."""

from __future__ import annotations

from inspect_ai.solver import Solver, TaskState, solver


@solver
def inject_rag_context() -> Solver:
    """Inject pre-computed RAG context into the prompt.

    Reads ``retrieved_contexts`` from the sample metadata and prepends
    them to the user's input as a context block.  This enables offline
    evaluation: the retrieval step is already done (by the dataset), and
    the model only needs to generate an answer given that context.
    """

    async def solve(state: TaskState, generate: object) -> TaskState:  # noqa: ARG001
        contexts = state.metadata.get("retrieved_contexts", [])
        if not contexts:
            return state

        context_block = "\n\n---\n\n".join(contexts)
        original_input = state.input_text

        augmented_input = (
            "Use the following context to answer the question. "
            "Only use information from the context. "
            "If the context does not contain enough information, say so.\n\n"
            f"## Context\n{context_block}\n\n"
            f"## Question\n{original_input}"
        )

        state.input_text = augmented_input
        return state

    return solve
