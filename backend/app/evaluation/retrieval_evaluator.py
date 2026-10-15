import json
import logging
from dataclasses import dataclass

from app.generation.llm import generate_text

logger = logging.getLogger(__name__)


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
You are evaluating retrieval quality in a retrieval-augmented
generation system.

Original question:
{original_query}

Information needs to cover:
{question_list}

Retrieved evidence:
{evidence}

Evaluate only what the evidence supports. Do not use outside knowledge.
A relevant chunk is not necessarily sufficient to answer a question.

Return only a valid JSON object with this exact structure:
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
- List unresolved information needs in missing_information.
- If evidence is empty, contradictory, or insufficient, reflect that in the scores.
""".strip()

    try:
        response = generate_text(prompt, max_output_tokens=512)
        result = json.loads(response)

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

        sufficient = (
            relevance >= min_relevance
            and coverage >= min_coverage
            and not missing
        )

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