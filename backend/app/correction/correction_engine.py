"""
correction_engine.py
~~~~~~~~~~~~~~~~~~~~~
High-level interface for query correction strategies.

This module coordinates:
1. Query decomposition (breaking complex questions into sub-queries)
2. Query expansion (synonym / rephrase variants)
3. Query rewriting (targeted improvement based on missing information)
"""

import logging
from typing import Callable, List, Optional

from app.correction.query_decomposer import decompose_query
from app.correction.query_expander import expand_query
from app.correction.query_rewriter import rewrite_query
from app.generation.llm import generate_text

logger = logging.getLogger(__name__)


def build_initial_queries(
    query: str,
    max_subqueries: int = 4,
    use_expansion: bool = False,
    generate: Optional[Callable[[str], str]] = None,
) -> List[str]:
    """
    Build the initial set of queries from a user's question.

    Steps:
    1. Decompose into focused sub-queries.
    2. Optionally expand with synonym/rephrasing variants.

    Args:
        query: Original user question.
        max_subqueries: Maximum decomposed sub-queries.
        use_expansion: Whether to also generate synonym-expanded variants.
        generate: LLM callable; defaults to generate_text.

    Returns:
        Deduplicated list of queries to retrieve against.
    """
    if not query or not query.strip():
        raise ValueError("query must not be empty")

    if generate is None:
        generate = generate_text

    original = query.strip()

    # Step 1: decompose
    try:
        subqueries = decompose_query(
            original,
            generate=generate,
            max_subqueries=max_subqueries,
        )
    except Exception:
        logger.exception("Decomposition failed; using original query")
        subqueries = [original]

    # Step 2: optional expansion
    if use_expansion:
        try:
            expansions = expand_query(original, generate=generate, max_expansions=2)
            # Only add new variants (not duplicates of decomposed queries)
            for exp in expansions[1:]:  # skip the original which is expansions[0]
                if exp not in subqueries:
                    subqueries.append(exp)
        except Exception:
            logger.exception("Query expansion failed; skipping")

    # Deduplicate while preserving order
    seen: set[str] = set()
    deduped: List[str] = []
    for q in subqueries:
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            deduped.append(q)

    return deduped or [original]


def build_correction_query(
    original_query: str,
    missing_information: Optional[List[str]] = None,
) -> str:
    """
    Build a corrected query when the initial retrieval was insufficient.

    Args:
        original_query: The user's original question.
        missing_information: Gaps identified by the retrieval evaluator.

    Returns:
        A rewritten query string targeting the missing information.
    """
    if not original_query or not original_query.strip():
        raise ValueError("original_query must not be empty")

    try:
        return rewrite_query(
            original_query=original_query,
            missing_information=missing_information,
        )
    except Exception:
        logger.exception("Query correction failed; returning original")
        return original_query.strip()