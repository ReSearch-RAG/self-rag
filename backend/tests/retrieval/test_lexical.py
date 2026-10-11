from unittest.mock import MagicMock

from app.db.models.chunk import Chunk
from app.retrieval.lexical import lexical_search


def test_lexical_search_returns_ranked_chunks():
    db = MagicMock()

    chunk_1 = Chunk(
        id=1,
        document_id=10,
        text="FastAPI is used for the backend.",
    )
    chunk_2 = Chunk(
        id=2,
        document_id=10,
        text="PostgreSQL stores application data.",
    )

    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
        (chunk_1, 0.85),
        (chunk_2, 0.42),
    ]

    results = lexical_search(
        db=db,
        query="FastAPI backend",
        document_id=10,
        top_k=5,
    )

    assert len(results) == 2
    assert results[0][0] is chunk_1
    assert results[0][1] == 0.85
    assert results[1][0] is chunk_2
    assert results[1][1] == 0.42


def test_lexical_search_returns_empty_results():
    db = MagicMock()

    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

    results = lexical_search(
        db=db,
        query="nonexistentterm",
        document_id=10,
        top_k=5,
    )

    assert results == []


def test_lexical_search_applies_top_k():
    db = MagicMock()

    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

    lexical_search(
        db=db,
        query="FastAPI",
        document_id=10,
        top_k=3,
    )

    db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_once_with(3)