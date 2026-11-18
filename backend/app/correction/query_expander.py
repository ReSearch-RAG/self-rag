"""
query_expander.py
~~~~~~~~~~~~~~~~~
Expand a user query with synonyms and related terms to improve recall,
especially for technical/domain-specific vocabulary.
"""

import json
import logging
import re
from typing import Callable, Optional

from app.generation.llm import generate_text

logger = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"```(?:json)?\s*|\s*```", re.IGNORECASE)


def expand_query(
    query: str,
    generate: Optional[Callable[[str], str]] = None,
    max_expansions: int = 3,
) -> list[str]:
    """
    Expand a query by generating related search terms and synonyms.

    Args:
        query: Original user query.
        generate: Callable that accepts a prompt string and returns generated text.
                  Defaults to the app's configured LLM (generate_text).
        max_expansions: Maximum number of expanded query variants to return.

    Returns:
        A list starting with the original query followed by expanded variants.
        Falls back to [original_query] if expansion fails.
    """
    if not query or not query.strip():
        raise ValueError("query must not be empty")

    if max_expansions < 1:
        raise ValueError("max_expansions must be at least 1")

    if generate is None:
        generate = generate_text

    original_query = query.strip()

    prompt = f"""
You are helping improve a search query for a research document retrieval system.

Original query:
{original_query}

Generate up to {max_expansions} alternative search queries that:
- Use different but related terminology or synonyms
- Rephrase the question from a different angle
- Include domain-specific terms that might appear in academic papers

Rules:
- Do not answer the question.
- Each alternative should be independently searchable.
- Return ONLY a valid JSON array of strings, no surrounding text.

Example output:
["alternative query one", "alternative query two"]
""".strip()

    try:
        response = generate(prompt)
        cleaned = _FENCE_RE.sub("", response).strip()
        parsed = json.loads(cleaned)

        if not isinstance(parsed, list):
            return [original_query]

        expansions = [
            item.strip()
            for item in parsed
            if isinstance(item, str) and item.strip() and item.strip() != original_query
        ][:max_expansions]

        return [original_query] + expansions

    except Exception:
        logger.exception("Query expansion failed; using original query only")
        return [original_query]