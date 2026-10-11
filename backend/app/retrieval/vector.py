from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk


def vector_search(
    db: Session,
    query_embedding: list[float],
    document_id: int,
    top_k: int = 5,
) -> list[Chunk]:
    return (
        db.query(Chunk)
        .filter(
            Chunk.document_id == document_id,
            Chunk.embedding.is_not(None),
        )
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
        .all()
    )