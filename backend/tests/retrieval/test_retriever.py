
from unittest.mock import patch

import pytest

from app.db.models.chunk import Chunk
from app.retrieval.retriever import retrieve


@pytest.fixture
def chunks():
    return [
        (Chunk(id=1, document_id=10, text="Chunk one"), 0.95),
        (Chunk(id=2, document_id=10, text="Chunk two"), 0.80),
    ]


def test_retrieve_runs_hybrid_search_then_reranking(chunks):
    with (
        patch(
            "app.retrieval.retriever.hybrid_search",
            return_value=chunks,
        ) as mock_hybrid,
        patch(
            "app.retrieval.retriever.rerank_chunks",
            return_value=[chunks[1], chunks[0]],
        ) as mock_rerank,
    ):
        results = retrieve(
            db=None,
            query="test query",
            query_embedding=[0.1] * 1024,
            document_id=10,
            top_k=2,
            candidate_k=20,
        )

    mock_hybrid.assert_called_once_with(
        db=None,
        query="test query",
        query_embedding=[0.1] * 1024,
        document_id=10,
        top_k=20,
        candidate_k=20,
    )

    mock_rerank.assert_called_once_with(
        query="test query",
        candidates=chunks,
        top_k=2,
    )

    assert results == [chunks[1], chunks[0]]


def test_retrieve_returns_empty_when_no_candidates():
    with (
        patch(
            "app.retrieval.retriever.hybrid_search",
            return_value=[],
        ) as mock_hybrid,
        patch(
            "app.retrieval.retriever.rerank_chunks",
        ) as mock_rerank,
    ):
        results = retrieve(
            db=None,
            query="test query",
            query_embedding=[0.1] * 1024,
            document_id=10,
        )

    assert results == []
    mock_rerank.assert_not_called()


def test_retrieve_rejects_empty_query():
    with pytest.raises(ValueError, match="query"):
        retrieve(
            db=None,
            query=" ",
            query_embedding=[0.1] * 1024,
            document_id=10,
        )


def test_retrieve_rejects_invalid_top_k():
    with pytest.raises(ValueError, match="top_k"):
        retrieve(
            db=None,
            query="test",
            query_embedding=[0.1] * 1024,
            document_id=10,
            top_k=0,
        )


def test_retrieve_rejects_invalid_candidate_k():
    with pytest.raises(ValueError, match="candidate_k"):
        retrieve(
            db=None,
            query="test",
            query_embedding=[0.1] * 1024,
            document_id=10,
            candidate_k=0,
        )
