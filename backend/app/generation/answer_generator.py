import logging
from typing import List, Tuple

from app.db.models.chunk import Chunk
from app.generation.context_builder import build_context
from app.generation.llm import generate_text

logger = logging.getLogger(__name__)


def generate_answer(
    query: str,
    chunks: List[Tuple[Chunk, float]],
    max_context_tokens: int = 6000,
) -> str:
    """Generate an evidence-grounded answer from retrieved chunks."""
    if not query or not query.strip():
        raise ValueError("query must not be empty")

    if not chunks:
        return (
            "I couldn't find relevant evidence in this document "
            "to answer your question."
        )

    context = build_context(chunks, max_tokens=max_context_tokens)

    if not context:
        return (
            "I couldn't find relevant evidence in this document "
            "to answer your question."
        )

    prompt = """You are a careful research-paper assistant.

Answer the user's question using only the evidence in the supplied document chunks.

Rules:
- Do not invent facts or use outside knowledge.
- If the evidence does not answer the question, explicitly state what is missing.
- Distinguish claims stated in the document from reasonable interpretations.
- Cite supporting evidence using chunk IDs, such as [Chunk 12].
- Do not fabricate citations.
- Give a clear, direct answer.

Document evidence:
{context}

User question:
{query}

Answer:""".format(
        context=context,
        query=query.strip(),
    )

    return generate_text(
        prompt=prompt,
        temperature=0.1,
        max_output_tokens=1024,
    )