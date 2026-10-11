from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk


def vector_search(
    db: Session,
    query_embedding: list[float],
    document_id: int,
    top_k: int = 5,
) -> list[tuple[Chunk, float]]:
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

    return [(chunk, float(score)) for chunk, score in results]
