from app.generation.llm import generate_text
from typing import Optional

def rewrite_query(
    original_query: str,
    missing_information: Optional[list[str]] = None,
) -> str:
    """Rewrite a query to improve retrieval when evidence is insufficient."""
    if not original_query or not original_query.strip():
        raise ValueError("original_query must not be empty")

    original_query = original_query.strip()
    missing_information = missing_information or []

    missing_context = (
        "\n".join(f"- {item}" for item in missing_information)
        if missing_information
        else "No specific gaps were provided."
    )

    prompt = f"""
You are improving a search query for a retrieval-augmented generation system.

Original question:
{original_query}

Information not adequately covered by retrieved evidence:
{missing_context}

Rewrite the question to improve retrieval.

Rules:
- Preserve the user's original intent.
- Incorporate missing information when it helps retrieval.
- Use clear, specific search language.
- Do not answer the question.
- Do not invent facts, entities, or assumptions.
- Return only the rewritten query as plain text.
""".strip()

    try:
        rewritten = generate_text(
            prompt,
            max_output_tokens=256,
        ).strip()

        if not rewritten:
            return original_query

        return rewritten

    except Exception:
        # Retrieval can still continue with the original question.
        return original_query