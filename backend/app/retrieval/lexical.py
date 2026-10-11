from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk


def lexical_search(
    db: Session,
    query: str,
    document_id: int,
    top_k: int = 5,
) -> list[tuple[Chunk, float]]:
    search_vector = func.to_tsvector("english", Chunk.text)
    search_query = func.plainto_tsquery("english", query)

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