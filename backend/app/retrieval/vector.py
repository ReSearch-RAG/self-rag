import logging

from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk

logger = logging.getLogger(__name__)


def vector_search(
    db: Session,
    query_embedding: list[float],
    document_id: int,
    top_k: int = 5,
) -> list[tuple[Chunk, float]]:
    """
    Retrieve chunks by cosine similarity.

    Returns (Chunk, similarity_score) pairs where higher score = more similar.
    Score is in [0, 1] range (converted from cosine distance).
    """
    distance = Chunk.embedding.cosine_distance(query_embedding).label(
        "cosine_distance"
    )

    results = (
        db.query(Chunk, distance)
        .filter(
            Chunk.document_id == document_id,
            Chunk.embedding.is_not(None),
        )
        .order_by(distance.asc())
        .limit(top_k)
        .all()
    )

    # Convert cosine distance [0, 2] → similarity [1, 0]
    # For unit-normalized vectors: similarity = 1 - dist/2
    return [
        (chunk, max(0.0, 1.0 - float(dist) / 2.0))
        for chunk, dist in results
    ]
