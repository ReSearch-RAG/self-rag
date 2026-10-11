
from unittest.mock import MagicMock

from app.db.models.chunk import Chunk
from app.retrieval.vector import vector_search


def test_vector_search_returns_ranked_chunks():
    db = MagicMock()

    chunk_1 = Chunk(
        id=1,
        document_id=10,
        text="Introduction to transformers.",
        embedding=[0.1] * 1024,
    )
    chunk_2 = Chunk(
        id=2,
        document_id=10,
        text="Introduction to recurrent neural networks.",
        embedding=[0.2] * 1024,
    )

    # Lower distance means a closer vector match.
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
        (chunk_1, 0.12),
        (chunk_2, 0.28),
    ]

    results = vector_search(
        db=db,
        query_embedding=[0.1] * 1024,
        document_id=10,
        top_k=5,
    )

    assert len(results) == 2
    assert results[0][0] is chunk_1
    assert results[1][0] is chunk_2
    assert results[0][1] < results[1][1]


def test_vector_search_returns_empty_results():
    db = MagicMock()

    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

    results = vector_search(
        db=db,
        query_embedding=[0.1] * 1024,
        document_id=10,
        top_k=5,
    )

    assert results == []


def test_vector_search_applies_top_k():
    db = MagicMock()

    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

    vector_search(
        db=db,
        query_embedding=[0.1] * 1024,
        document_id=10,
        top_k=3,
    )

    db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_once_with(3)
