"""
claim_extractor.py
~~~~~~~~~~~~~~~~~~
Extract atomic factual claims from a generated answer so they can
be individually verified against the retrieved evidence.
"""

import json
import logging
import re

from app.generation.llm import generate_text

logger = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"```(?:json)?\s*|\s*```", re.IGNORECASE)


def extract_claims(answer: str, max_claims: int = 10) -> list[str]:
    """
    Extract a list of atomic, verifiable factual claims from a generated answer.

    Args:
        answer: The generated answer text.
        max_claims: Maximum number of claims to extract.

    Returns:
        A list of claim strings. Falls back to [answer] if extraction fails.
    """
    if not answer or not answer.strip():
        raise ValueError("answer must not be empty")

    if max_claims < 1:
        raise ValueError("max_claims must be at least 1")

    prompt = f"""
You are extracting factual claims from a research-paper assistant's answer.

Answer:
{answer.strip()}

Extract up to {max_claims} distinct, atomic, verifiable factual claims from the answer.
Each claim should be a single sentence that can be independently checked against evidence.

Rules:
- Only extract claims that assert specific facts.
- Do not include hedges like "the document states" — extract the core factual content.
- Do not include questions or instructions.
- Return ONLY a valid JSON array of strings, no surrounding text.

Example output:
["The model achieves 92% accuracy on MNIST.", "Training was performed on 4 A100 GPUs."]
""".strip()

    try:
        response = generate_text(prompt, max_output_tokens=512)
        cleaned = _FENCE_RE.sub("", response).strip()
        parsed = json.loads(cleaned)

        if not isinstance(parsed, list):
            return [answer.strip()]

        claims = [
            item.strip()
            for item in parsed
            if isinstance(item, str) and item.strip()
        ][:max_claims]

        return claims or [answer.strip()]

    except Exception:
        logger.exception("Claim extraction failed; returning full answer as single claim")
        return [answer.strip()]
