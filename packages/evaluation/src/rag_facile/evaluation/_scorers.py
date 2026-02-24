"""Inspect AI scorers for rag-facile RAG pipeline evaluation.

Two scorers measuring answer quality:

- :func:`faithfulness`        — LLM-as-judge: is the answer grounded in the
                                retrieved context?
- :func:`answer_correctness`  — LLM-as-judge: does the answer match the
                                reference answer?
- :func:`rag_eval_scorer`     — combined multi-value scorer (both above)

Legacy chunk-ID scorers (:func:`recall_at_k`, :func:`precision_at_k`) are
kept for advanced use-cases where stable chunk IDs are available, but are
not included in the default combined scorer.
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


# ── Judge prompts ─────────────────────────────────────────────────────────────

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

ANSWER_CORRECTNESS_TEMPLATE = """\
You are evaluating whether a model answer correctly addresses a question \
compared to a reference answer.

## Question
{question}

## Reference Answer
{reference}

## Model Answer
{answer}

## Instructions
1. List the key facts in the reference answer (one per line, prefixed with "- ").
2. For each key fact, state whether the model answer COVERS or MISSES it.
3. Finally, output a single line:
   SCORE: <float between 0.0 and 1.0>
   where 1.0 means all key facts are covered and 0.0 means none are.

Be fair: accept paraphrases and equivalent expressions, not just exact matches.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────


def _parse_score(text: str) -> float:
    """Extract the SCORE: <float> from judge output, clamped to [0, 1]."""
    match = re.search(r"SCORE:\s*([\d.]+)", text, re.IGNORECASE)
    if match:
        value = float(match.group(1))
        return max(0.0, min(1.0, value))
    return 0.0


# Keep old name as alias for backwards compatibility with tests
_parse_faithfulness_score = _parse_score


# ── Primary scorers ───────────────────────────────────────────────────────────


@scorer(metrics=[mean(), stderr()])
def faithfulness(model: str | None = None) -> Scorer:
    """LLM-as-judge: is the model's answer grounded in the retrieved context?

    Reads ``retrieved_contexts`` from ``state.metadata`` (set by the
    ``retrieve_rag_context`` solver).  Returns 1.0 (vacuously true) when no
    context is available — faithfulness is meaningless without context.

    Args:
        model: Grader model identifier (e.g. ``"openai/openweight-medium"``).
            When *None*, uses the task's default model.
    """

    async def score(state: TaskState, target: Target) -> Score:  # noqa: ARG001
        contexts = state.metadata.get("retrieved_contexts", [])
        context = "\n\n---\n\n".join(contexts) if contexts else ""
        answer = state.output.completion if state.output else ""

        if not answer:
            return Score(value=0.0, explanation="No answer generated")
        if not context:
            return Score(
                value=1.0,
                explanation="No context retrieved — faithfulness check skipped",
            )

        prompt = FAITHFULNESS_TEMPLATE.format(context=context, answer=answer)
        grader = get_model(model) if model else get_model()
        result = await grader.generate(prompt, config=GenerateConfig(temperature=0.0))
        judge_output = result.completion

        return Score(value=_parse_score(judge_output), explanation=judge_output)

    return score


@scorer(metrics=[mean(), stderr()])
def answer_correctness(model: str | None = None) -> Scorer:
    """LLM-as-judge: does the model's answer match the reference answer?

    Compares the generated answer against the ground-truth reference stored
    in the Inspect AI ``Target``.  Returns 1.0 (vacuously true) when no
    reference is available.

    Args:
        model: Grader model identifier (e.g. ``"openai/openweight-medium"``).
            When *None*, uses the task's default model.
    """

    async def score(state: TaskState, target: Target) -> Score:
        question = state.input_text
        reference = target.target if hasattr(target, "target") else str(target)
        answer = state.output.completion if state.output else ""

        if not answer:
            return Score(value=0.0, explanation="No answer generated")
        if not reference:
            return Score(
                value=1.0, explanation="No reference answer — correctness check skipped"
            )

        prompt = ANSWER_CORRECTNESS_TEMPLATE.format(
            question=question,
            reference=reference,
            answer=answer,
        )
        grader = get_model(model) if model else get_model()
        result = await grader.generate(prompt, config=GenerateConfig(temperature=0.0))
        judge_output = result.completion

        return Score(value=_parse_score(judge_output), explanation=judge_output)

    return score


# ── Combined scorer ───────────────────────────────────────────────────────────
# Note: For multiple metrics, use scorer=[faithfulness(model=...), answer_correctness(model=...)]
# in the Task definition rather than a combined scorer. This gives each metric
# its own row in the results.


def rag_eval_scorer(model: str | None = None) -> list[Scorer]:
    """Return a list of all RAG evaluation scorers.

    Convenience function returning [faithfulness, answer_correctness].
    For Inspect AI, pass this as ``scorer=rag_eval_scorer(model)``.
    """
    return [faithfulness(model=model), answer_correctness(model=model)]
    """Combined RAG evaluation scorer: faithfulness + answer correctness.

    Returns a multi-value score dict so Inspect AI tracks both metrics
    separately in the log.

    Args:
        model: Model identifier for both LLM-as-judge scorers.
    """
    _faithful = faithfulness(model=model)
    _correct = answer_correctness(model=model)

    async def score(state: TaskState, target: Target) -> Score:
        f = await _faithful(state, target)
        c = await _correct(state, target)

        f_val = float(f.value) if isinstance(f.value, (int, float)) else 0.0
        c_val = float(c.value) if isinstance(c.value, (int, float)) else 0.0

        return Score(
            value={
                "faithfulness": f_val,
                "answer_correctness": c_val,
            },
            explanation=(f"faithfulness={f_val:.2f} answer_correctness={c_val:.2f}"),
        )

    return score


# ── Legacy chunk-ID scorers ───────────────────────────────────────────────────
# Kept for advanced use-cases where stable chunk IDs are available in the
# dataset.  Not included in rag_eval_scorer.


@scorer(metrics=[mean(), stderr()])
def recall_at_k() -> Scorer:
    """Fraction of relevant chunks found in retrieved results.

    Requires ``relevant_chunk_ids`` and ``retrieved_chunk_ids`` in sample
    metadata.  Returns 1.0 (vacuously true) when no relevant IDs are defined.
    """

    async def score(state: TaskState, target: Target) -> Score:  # noqa: ARG001
        retrieved = set(state.metadata.get("retrieved_chunk_ids", []))
        relevant = set(state.metadata.get("relevant_chunk_ids", []))

        if not relevant:
            return Score(
                value=1.0,
                explanation="No relevant chunk IDs defined — vacuously true",
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

    Requires ``relevant_chunk_ids`` and ``retrieved_chunk_ids`` in sample
    metadata.  Returns 1.0 (vacuously true) when no chunk IDs are defined.
    """

    async def score(state: TaskState, target: Target) -> Score:  # noqa: ARG001
        retrieved = set(state.metadata.get("retrieved_chunk_ids", []))
        relevant = set(state.metadata.get("relevant_chunk_ids", []))

        if not retrieved:
            return Score(
                value=1.0,
                explanation="No chunk IDs defined — vacuously true",
            )

        hits = relevant & retrieved
        precision = len(hits) / len(retrieved)
        return Score(
            value=precision,
            explanation=f"{len(hits)}/{len(retrieved)} retrieved chunks are relevant",
        )

    return score
