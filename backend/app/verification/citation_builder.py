"""
citation_builder.py
~~~~~~~~~~~~~~~~~~~
Format retrieved chunk references into human-readable citations.
"""

import logging
from typing import List, Tuple

from app.db.models.chunk import Chunk

logger = logging.getLogger(__name__)


def build_citation_text(chunk_id: int, chunks: List[Tuple[Chunk, float]]) -> str:
    """
    Build a human-readable citation string for a given chunk ID.

    Args:
        chunk_id: The chunk ID referenced in the answer.
        chunks: The full list of (Chunk, score) pairs from retrieval.

    Returns:
        A formatted citation string like "[Chunk 42, Page 7, Section: Methods]".
    """
    for chunk, _ in chunks:
        if chunk.id == chunk_id:
            page = chunk.page_number or "unknown"
            section = chunk.section or "unknown"
            return f"[Chunk {chunk_id}, Page {page}, Section: {section}]"

    return f"[Chunk {chunk_id}]"


def build_citations(
    answer: str,
    chunks: List[Tuple[Chunk, float]],
) -> str:
    """
    Append a formatted citation list to the answer for all chunk IDs
    referenced in the text.

    Args:
        answer: The generated answer text (may contain [Chunk X] references).
        chunks: Retrieved (Chunk, score) pairs.

    Returns:
        Answer text with an appended "References" section.
    """
    import re

    # Find all [Chunk N] references in the answer
    referenced_ids = set(
        int(m) for m in re.findall(r"\[Chunk\s+(\d+)\]", answer, re.IGNORECASE)
    )

    if not referenced_ids:
        return answer

    chunk_map = {chunk.id: chunk for chunk, _ in chunks}

    citation_lines: List[str] = []
    for chunk_id in sorted(referenced_ids):
        chunk = chunk_map.get(chunk_id)
        if chunk:
            page = chunk.page_number or "unknown"
            section = chunk.section or "unknown"
            citation_lines.append(
                f"  [Chunk {chunk_id}] Page {page} | Section: {section}"
            )
        else:
            logger.warning("Answer references unknown Chunk %d", chunk_id)

    if citation_lines:
        refs = "\n".join(citation_lines)
        return f"{answer}\n\n**References:**\n{refs}"

    return answer
