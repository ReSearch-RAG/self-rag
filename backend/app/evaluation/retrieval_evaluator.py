import json
import logging
import re
import time
from dataclasses import dataclass

from app.generation.llm import generate_text

logger = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"```(?:json)?\s*|\s*```", re.IGNORECASE)


def _strip_fences(text: str) -> str:
    """Remove markdown code fences that Gemini sometimes wraps JSON in."""
    return _FENCE_RE.sub("", text).strip()


def _parse_evaluation_response(raw: str) -> dict:
    """Parse and validate the LLM evaluation JSON response."""
    cleaned = _strip_fences(raw)
    result = json.loads(cleaned)

    relevance = float(result["relevance_score"])
    coverage = float(result["coverage_score"])
    missing = result["missing_information"]
    reason = result["reason"]

    if not 0 <= relevance <= 1 or not 0 <= coverage <= 1:
        raise ValueError("Evaluation scores must be between 0 and 1")

    if not isinstance(missing, list) or not all(
        isinstance(item, str) for item in missing
    ):
        raise ValueError("missing_information must be a list of strings")

    if not isinstance(reason, str):
        raise ValueError("reason must be a string")

    return {
        "relevance_score": relevance,
        "coverage_score": coverage,
        "missing_information": missing,
        "reason": reason,
    }


def _call_evaluator_with_retry(prompt: str, max_attempts: int = 3) -> dict:
    """Call the LLM evaluator with simple exponential backoff on failure."""
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = generate_text(prompt, max_output_tokens=512)
            return _parse_evaluation_response(response)
        except Exception as exc:
            last_exc = exc
            if attempt < max_attempts:
                wait = 2 ** (attempt - 1)  # 1s, 2s
                logger.warning(
                    "Evaluation attempt %d/%d failed (%s), retrying in %ds",
                    attempt, max_attempts, exc, wait,
                )
                time.sleep(wait)

    raise last_exc  # type: ignore[misc]


@dataclass
class RetrievalEvaluation:
    is_sufficient: bool
    relevance_score: float
    coverage_score: float
    missing_information: list[str]
    reason: str


def evaluate_retrieval(
    original_query: str,
    subqueries: list[str],
    chunks: list[tuple],
    min_relevance: float = 0.6,
    min_coverage: float = 0.7,
) -> RetrievalEvaluation:
    """Evaluate whether retrieved evidence is relevant and sufficiently complete."""

    if not original_query or not original_query.strip():
        raise ValueError("original_query must not be empty")

    if not 0 <= min_relevance <= 1:
        raise ValueError("min_relevance must be between 0 and 1")

    if not 0 <= min_coverage <= 1:
        raise ValueError("min_coverage must be between 0 and 1")

    if not chunks:
        return RetrievalEvaluation(
            is_sufficient=False,
            relevance_score=0.0,
            coverage_score=0.0,
            missing_information=subqueries or [original_query.strip()],
            reason="No evidence was retrieved.",
        )

    evidence = "\n\n".join(
        f"[Chunk {chunk.id}]\n{chunk.text[:3000]}"
        for chunk, _ in chunks[:10]
    )

    questions = subqueries or [original_query.strip()]
    question_list = "\n".join(
        f"- {question}" for question in questions
    )

    prompt = f"""
You are evaluating retrieval quality in a retrieval-augmented generation system.

Original question:
{original_query}

Information needs to cover:
{question_list}

Retrieved evidence:
{evidence}

Evaluate only what the evidence supports. Do not use outside knowledge.
A relevant chunk is not necessarily sufficient to answer a question.

Return ONLY a valid JSON object with no surrounding text or markdown, using this exact structure:
{{
  "relevance_score": 0.0,
  "coverage_score": 0.0,
  "missing_information": ["information not supported by the evidence"],
  "reason": "brief explanation"
}}

Rules:
- Scores must be numbers between 0.0 and 1.0.
- Relevance measures how relevant the evidence is to the original question.
- Coverage measures how many information needs are adequately supported.
- List unresolved information needs in missing_information. Use an empty list [] if all needs are covered.
- If evidence is empty, contradictory, or insufficient, reflect that in the scores.
""".strip()

    try:
        result = _call_evaluator_with_retry(prompt)

        relevance = result["relevance_score"]
        coverage = result["coverage_score"]
        missing = result["missing_information"]
        reason = result["reason"]

        # Sufficiency is based solely on numeric thresholds.
        # missing_information is advisory context for the rewriter — not a gate.
        sufficient = relevance >= min_relevance and coverage >= min_coverage

        return RetrievalEvaluation(
            is_sufficient=sufficient,
            relevance_score=relevance,
            coverage_score=coverage,
            missing_information=missing,
            reason=reason,
        )

    except Exception:
        logger.exception(
            "Retrieval evaluation failed; treating evidence as unverified"
        )

        return RetrievalEvaluation(
            is_sufficient=False,
            relevance_score=0.0,
            coverage_score=0.0,
            missing_information=questions,
            reason="Evaluation failed; evidence sufficiency could not be verified.",
        )