
from unittest.mock import patch

import pytest

from app.db.models.chunk import Chunk
from app.retrieval.hybrid import hybrid_search


@pytest.fixture
def chunks():
    return [
        Chunk(id=1, document_id=10, text="Chunk one"),
        Chunk(id=2, document_id=10, text="Chunk two"),
        Chunk(id=3, document_id=10, text="Chunk three"),
    ]


def test_hybrid_search_combines_vector_and_lexical_results(chunks):
    vector_results = [
        (chunks[0], 0.10),
        (chunks[1], 0.20),
    ]

    lexical_results = [
        (chunks[1], 0.90),
        (chunks[2], 0.70),
    ]

    with (
        patch(
            "app.retrieval.hybrid.vector_search",
            return_value=vector_results,
        ),
        patch(
            "app.retrieval.hybrid.lexical_search",
            return_value=lexical_results,
        ),
    ):
        results = hybrid_search(
            db=None,
            query="test query",
            query_embedding=[0.1] * 1024,
            document_id=10,
            top_k=3,
        )

    result_ids = [chunk.id for chunk, score in results]

    # Chunk 2 appears in both retrieval lists, so it ranks first.
    assert result_ids[0] == 2
    assert set(result_ids) == {1, 2, 3}

    # Fused scores should be descending.
    scores = [score for chunk, score in results]
    assert scores == sorted(scores, reverse=True)


def test_hybrid_search_respects_top_k(chunks):
    vector_results = [
        (chunks[0], 0.10),
        (chunks[1], 0.20),
        (chunks[2], 0.30),
    ]

    with (
        patch(
            "app.retrieval.hybrid.vector_search",
            return_value=vector_results,
        ),
        patch(
            "app.retrieval.hybrid.lexical_search",
            return_value=[],
        ),
    ):
        results = hybrid_search(
            db=None,
            query="test query",
            query_embedding=[0.1] * 1024,
            document_id=10,
            top_k=2,
        )

    assert len(results) == 2


def test_hybrid_search_handles_no_results():
    with (
        patch("app.retrieval.hybrid.vector_search", return_value=[]),
        patch("app.retrieval.hybrid.lexical_search", return_value=[]),
    ):
        results = hybrid_search(
            db=None,
            query="no matches",
            query_embedding=[0.1] * 1024,
            document_id=10,
            top_k=5,
        )

    assert results == []


def test_hybrid_search_rejects_invalid_top_k():
    with pytest.raises(ValueError, match="top_k"):
        hybrid_search(
            db=None,
            query="test",
            query_embedding=[0.1] * 1024,
            document_id=10,
            top_k=0,
        )
