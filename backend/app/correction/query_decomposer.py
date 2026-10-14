import json
from typing import Callable


def decompose_query(
    query: str,
    generate: Callable[[str], str],
    max_subqueries: int = 4,
) -> list[str]:
    """
    Decompose a complex query into smaller, searchable subqueries.

    Args:
        query: Original user question.
        generate: Callable that accepts a prompt and returns generated text.
        max_subqueries: Maximum number of subqueries to return.

    Returns:
        A list of subqueries. Falls back to the original query
        if decomposition fails or produces no valid subqueries.
    """
    if not query or not query.strip():
        raise ValueError("query must not be empty")

    if max_subqueries < 1:
        raise ValueError("max_subqueries must be at least 1")

    original_query = query.strip()

    prompt = f"""
Break the following question into at most {max_subqueries} independent,
searchable subqueries.

Rules:
- Preserve the original question's intent.
- Make each subquery understandable on its own.
- Do not answer the questions.
- Return only a valid JSON array of strings.

Question:
{original_query}
""".strip()

    try:
        response = generate(prompt)
        parsed = json.loads(response)

        if not isinstance(parsed, list):
            return [original_query]

        subqueries = []
        for item in parsed:
            if isinstance(item, str) and item.strip():
                cleaned = item.strip()
                if cleaned not in subqueries:
                    subqueries.append(cleaned)

            if len(subqueries) >= max_subqueries:
                break

        return subqueries or [original_query]

    except (ValueError, TypeError):
        return [original_query]