"""
claim_verifier.py
~~~~~~~~~~~~~~~~~
Verify individual factual claims against retrieved document chunks.
Thin wrapper around evidence.verify_claim that handles a list of claims.
"""

import logging
from typing import List, Tuple

from app.db.models.chunk import Chunk
from app.evaluation.evidence import EvidenceVerification, verify_claim

logger = logging.getLogger(__name__)


def verify_claims(
    claims: List[str],
    chunks: List[Tuple[Chunk, float]],
) -> List[EvidenceVerification]:
    """
    Verify a list of claims against retrieved chunks.

    Args:
        claims: List of atomic factual claims to verify.
        chunks: (Chunk, score) pairs to use as evidence.

    Returns:
        List of EvidenceVerification results, one per claim.
    """
    results: List[EvidenceVerification] = []

    for claim in claims:
        if not claim or not claim.strip():
            logger.warning("Skipping empty claim")
            continue

        try:
            result = verify_claim(claim=claim, chunks=chunks)
            results.append(result)
            logger.debug(
                "Claim verified: verdict=%s claim=%r",
                result.verdict,
                claim[:80],
            )
        except Exception:
            logger.exception("Failed to verify claim: %r", claim[:80])
            results.append(
                EvidenceVerification(
                    verdict="insufficient",
                    supporting_chunk_ids=[],
                    contradicting_chunk_ids=[],
                    explanation="Verification failed for this claim.",
                )
            )

    return results
