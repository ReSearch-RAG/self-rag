import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk

logger = logging.getLogger(__name__)


def lexical_search(
    db: Session,
    query: str,
    document_id: int,
    top_k: int = 5,
) -> list[tuple[Chunk, float]]:
    """
    Full-text search using PostgreSQL ts_rank.

    Uses websearch_to_tsquery (PostgreSQL 11+) which supports:
    - Quoted phrases: "neural network"
    - Negation: -word
    - OR logic: cat OR dog
    This is strictly more capable than plainto_tsquery.
    """
    search_vector = func.to_tsvector("english", Chunk.text)
    # websearch_to_tsquery handles phrases and boolean operators
    search_query = func.websearch_to_tsquery("english", query)

    rank = func.ts_rank(search_vector, search_query).label("rank")

    results = (
        db.query(Chunk, rank)
        .filter(
            Chunk.document_id == document_id,
            search_vector.op("@@")(search_query),
        )
        .order_by(rank.desc())
        .limit(top_k)
        .all()
    )

    return [(chunk, float(score)) for chunk, score in results]
