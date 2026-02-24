"""RAG evaluation scorers for Inspect AI.

Three scorers measuring retrieval quality and answer faithfulness:

- :func:`recall_at_k` — fraction of relevant chunks actually retrieved
- :func:`precision_at_k` — fraction of retrieved chunks that are relevant
- :func:`faithfulness` — LLM-as-judge: is the answer grounded in context?
- :func:`rag_eval_scorer` — combined multi-value scorer (all three)
"""

from __future__ import annotations

import re

from inspect_ai.model import GenerateConfig, get_model
from inspect_ai.scorer import (
    Score,
    Scorer,
    Target,
    mean,
    scorer,
    stderr,
)
from inspect_ai.solver import TaskState


# ── Faithfulness prompt ──────────────────────────────────────────────────────

FAITHFULNESS_TEMPLATE = """\
You are an impartial judge evaluating whether an answer is faithful to the \
provided context. An answer is faithful if every claim it makes is supported \
by the context. Invented or hallucinated information is NOT faithful.

## Context
{context}

## Answer
{answer}

## Instructions
1. List each factual claim in the answer (one per line, prefixed with "- ").
2. For each claim, state whether it is SUPPORTED or NOT SUPPORTED by the context.
3. Finally, output a single line:
   SCORE: <float between 0.0 and 1.0>
   where 1.0 means all claims are supported and 0.0 means none are.

Be strict: if a claim adds information not present in the context, mark it NOT SUPPORTED.
"""


# ── Helpers ──────────────────────────────────────────────────────────────────


def _parse_faithfulness_score(text: str) -> float:
    """Extract the SCORE: <float> from the judge output."""
    match = re.search(r"SCORE:\s*([\d.]+)", text, re.IGNORECASE)
    if match:
        value = float(match.group(1))
        return max(0.0, min(1.0, value))  # clamp
    return 0.0


# ── Scorers ──────────────────────────────────────────────────────────────────


@scorer(metrics=[mean(), stderr()])
def recall_at_k() -> Scorer:
    """Fraction of ground-truth relevant chunks found in retrieved results.

    Reads ``relevant_chunk_ids`` and ``retrieved_chunk_ids`` from sample
    metadata.  Returns 1.0 when all relevant chunks were retrieved, 0.0 when
    none were.  If no relevant chunks are defined, returns 1.0 (vacuously true).
    """

    async def score(state: TaskState, target: Target) -> Score:
        retrieved = set(state.metadata.get("retrieved_chunk_ids", []))
        relevant = set(state.metadata.get("relevant_chunk_ids", []))

        if not relevant:
            return Score(
                value=1.0,
                explanation="No relevant chunks defined — vacuously true",
            )

        hits = relevant & retrieved
        recall = len(hits) / len(relevant)
        return Score(
            value=recall,
            explanation=f"{len(hits)}/{len(relevant)} relevant chunks retrieved",
        )

    return score


@scorer(metrics=[mean(), stderr()])
def precision_at_k() -> Scorer:
    """Fraction of retrieved chunks that are relevant.

    Reads ``relevant_chunk_ids`` and ``retrieved_chunk_ids`` from sample
    metadata.  Returns 0.0 when nothing was retrieved.
    """

    async def score(state: TaskState, target: Target) -> Score:
        retrieved = set(state.metadata.get("retrieved_chunk_ids", []))
        relevant = set(state.metadata.get("relevant_chunk_ids", []))

        if not retrieved:
            return Score(
                value=0.0,
                explanation="No chunks retrieved",
            )

        hits = relevant & retrieved
        precision = len(hits) / len(retrieved)
        return Score(
            value=precision,
            explanation=(f"{len(hits)}/{len(retrieved)} retrieved chunks are relevant"),
        )

    return score


@scorer(metrics=[mean(), stderr()])
def faithfulness(model: str | None = None) -> Scorer:
    """LLM-as-judge scorer for answer faithfulness.

    Asks a grader model to decompose the answer into claims and check each
    against the provided context.  Returns a score between 0.0 (no claims
    supported) and 1.0 (all claims supported).

    Args:
        model: Model identifier for the grader (e.g. ``"openai/openweight-medium"``).
            When *None*, uses the task's default model.
    """

    async def score(state: TaskState, target: Target) -> Score:
        contexts = state.metadata.get("retrieved_contexts", [])
        context = "\n\n---\n\n".join(contexts) if contexts else ""
        answer = state.output.completion if state.output else ""

        if not answer:
            return Score(value=0.0, explanation="No answer generated")

        if not context:
            return Score(
                value=0.0,
                explanation="No context available — cannot judge faithfulness",
            )

        grader = get_model(model)
        prompt = FAITHFULNESS_TEMPLATE.format(context=context, answer=answer)
        result = await grader.generate(
            input=prompt,
            config=GenerateConfig(temperature=0.0),
        )

        judge_output = result.completion if result else ""
        parsed_score = _parse_faithfulness_score(judge_output)

        return Score(
            value=parsed_score,
            answer=answer,
            explanation=judge_output,
        )

    return score


@scorer(
    metrics={
        "recall": [mean(), stderr()],
        "precision": [mean(), stderr()],
        "faithfulness": [mean(), stderr()],
    }
)
def rag_eval_scorer(model: str | None = None) -> Scorer:
    """Combined RAG evaluation scorer returning all three metrics.

    Computes recall@k, precision@k, and faithfulness in a single pass.

    Args:
        model: Model identifier for the faithfulness grader.
    """
    _recall = recall_at_k()
    _precision = precision_at_k()
    _faithful = faithfulness(model=model)

    async def score(state: TaskState, target: Target) -> Score:
        r = await _recall(state, target)
        p = await _precision(state, target)
        f = await _faithful(state, target)

        return Score(
            value={
                "recall": r.value,
                "precision": p.value,
                "faithfulness": f.value,
            },
            explanation=(
                f"recall={r.value:.2f} precision={p.value:.2f} "
                f"faithfulness={f.value:.2f}"
            ),
        )

    return score
