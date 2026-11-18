import logging

from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk
from app.ingestion.chunker import chunk_pages
from app.ingestion.embedder import get_embedder
from app.ingestion.normalizer import normalize_pages
from app.ingestion.parser import parse_pdf

logger = logging.getLogger(__name__)


def ingest_document(
    db: Session,
    document_id: int,
    file_path: str,
) -> list[Chunk]:
    pages = parse_pdf(file_path)

    normalized_pages = normalize_pages(pages)

    chunks = chunk_pages(normalized_pages)

    if not chunks:
        logger.warning("No chunks produced for document_id=%d", document_id)
        return []

    embedder = get_embedder()

    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedder.embed(texts)

    chunk_records = []

    for chunk, embedding in zip(chunks, embeddings):
        chunk_record = Chunk(
            document_id=document_id,
            text=chunk["text"],
            page_number=chunk["page_number"],
            section=chunk.get("section"),
            embedding=embedding,
        )

        db.add(chunk_record)
        chunk_records.append(chunk_record)

    db.commit()

    logger.info(
        "Ingested %d chunks for document_id=%d",
        len(chunk_records),
        document_id,
    )
    return chunk_records
