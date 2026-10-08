from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk
from app.ingestion.chunker import chunk_pages
from app.ingestion.embedder import Embedder
from app.ingestion.normalizer import normalize_pages
from app.ingestion.parser import parse_pdf


def ingest_document(
    db: Session,
    document_id: int,
    file_path: str,
) -> list[Chunk]:
    pages = parse_pdf(file_path)

    normalized_pages = normalize_pages(pages)

    chunks = chunk_pages(normalized_pages)

    embedder = Embedder()

    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedder.embed(texts)

    chunk_records = []

    for chunk, embedding in zip(chunks, embeddings):
        chunk_record = Chunk(
            document_id=document_id,
            text=chunk["text"],
            page_number=chunk["page_number"],
            section=chunk["section"],
            embedding=embedding,
        )

        db.add(chunk_record)
        chunk_records.append(chunk_record)

    db.commit()

    return chunk_records