import logging
from typing import List, Tuple

from app.db.models.chunk import Chunk
from app.generation.context_builder import build_context
from app.generation.llm import generate_text

logger = logging.getLogger(__name__)


def generate_document_summary(
    document_name: str,
    chunks: List[Tuple[Chunk, float]],
    max_context_tokens: int = 8000,
) -> str:
    """Generate a grounded overview of a document from representative chunks."""
    if not chunks:
        raise ValueError("chunks must not be empty")

    context = build_context(chunks, max_tokens=max_context_tokens)
    if not context:
        raise ValueError("No usable document context was found")

    prompt = """You are summarizing a PDF for the user.

Document name: {document_name}

Rules:
- Base the summary only on the supplied document evidence.
- Describe the document's purpose, main topics, and key findings or features.
- Cite supporting evidence using chunk IDs, such as [Chunk 12].
- Do not invent facts or use outside knowledge.
- If the excerpt is insufficient for a complete overview, state that clearly.
- Keep the response concise but useful.

Document evidence:
{context}

Provide a clear overview of what this PDF is about:""".format(
        document_name=document_name,
        context=context,
    )

    return generate_text(
        prompt=prompt,
        temperature=0.2,
        max_output_tokens=1024,
    )


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