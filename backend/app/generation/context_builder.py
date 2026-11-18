"""
context_builder.py
~~~~~~~~~~~~~~~~~~
Assembles retrieved chunks into a prompt-ready context string.

Responsibilities:
- Deduplicate chunks with significant text overlap (from chunker's sliding window).
- Order chunks by reranker score (highest first).
- Enforce a token budget so the context never overflows the LLM context window.
- Format each chunk with metadata for citation.
"""

import logging

from app.db.models.chunk import Chunk
from app.ingestion.embedder import get_embedder

logger = logging.getLogger(__name__)

# Conservative token budget for the evidence section of the prompt.
# Leaves room for the system prompt, question, and answer (~4000 tokens).
DEFAULT_MAX_CONTEXT_TOKENS = 6000


def _has_significant_overlap(a: str, b: str, threshold: float = 0.6) -> bool:
    """
    Return True if two chunk texts share more than `threshold` fraction
    of their content (Jaccard similarity on word sets).
    """
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return False
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union) >= threshold


def _deduplicate_chunks(
    chunks: list[tuple[Chunk, float]],
    overlap_threshold: float = 0.6,
) -> list[tuple[Chunk, float]]:
    """
    Remove chunks whose text substantially overlaps with a higher-scoring chunk.
    Assumes chunks are already sorted by score descending.
    """
    seen: list[str] = []
    deduped: list[tuple[Chunk, float]] = []

    for chunk, score in chunks:
        text = chunk.text
        if any(_has_significant_overlap(text, s, overlap_threshold) for s in seen):
            logger.debug("Deduplicating overlapping chunk id=%d", chunk.id)
            continue
        seen.append(text)
        deduped.append((chunk, score))

    return deduped


def build_context(
    chunks: list[tuple[Chunk, float]],
    max_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
    overlap_threshold: float = 0.6,
) -> str:
    """
    Build a formatted context string from retrieved chunks.

    Args:
        chunks: (Chunk, score) pairs, sorted by score descending.
        max_tokens: Maximum number of tokens the context may use.
        overlap_threshold: Jaccard threshold above which a chunk is considered
                           a duplicate of an already-included chunk.

    Returns:
        A formatted string ready to be inserted into the generation prompt.
    """
    if not chunks:
        return ""

    embedder = get_embedder()
    deduped = _deduplicate_chunks(chunks, overlap_threshold)

    parts: list[str] = []
    total_tokens = 0

    for chunk, score in deduped:
        header = "[Chunk ID: {} | Page: {} | Section: {}]".format(
            chunk.id,
            chunk.page_number or "Unknown",
            chunk.section or "Unknown",
        )
        block = f"{header}\n{chunk.text}"
        block_tokens = embedder.count_tokens(block)

        if total_tokens + block_tokens > max_tokens:
            logger.debug(
                "Token budget reached at chunk id=%d (%d tokens used, budget=%d)",
                chunk.id, total_tokens, max_tokens,
            )
            break

        parts.append(block)
        total_tokens += block_tokens

    logger.debug(
        "Context built: %d/%d chunks included, ~%d tokens",
        len(parts), len(deduped), total_tokens,
    )

    return "\n\n".join(parts)
