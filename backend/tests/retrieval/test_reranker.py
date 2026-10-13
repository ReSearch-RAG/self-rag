
from unittest.mock import patch

import pytest

from app.db.models.chunk import Chunk
from app.retrieval.reranker import rerank_chunks


@pytest.fixture
def candidates():
    chunk1 = Chunk(id=1, document_id=10, text="Python is a programming language.")
    chunk2 = Chunk(id=2, document_id=10, text="Tokens expire after their validity period.")
    chunk3 = Chunk(id=3, document_id=10, text="The database stores user records.")

    # The second value is the previous retrieval score.
    return [
        (chunk1, 0.03),
        (chunk2, 0.02),
        (chunk3, 0.01),
    ]


def test_reranker_sorts_by_relevance(candidates):
    # Scores correspond to candidates in their original order.
    mock_model = patch(
        "app.retrieval.reranker.get_reranker"
    )

    with mock_model as get_model:
        get_model.return_value.compute_score.return_value = [
            0.2, 0.95, 0.1
        ]

        results = rerank_chunks(
            query="When do tokens expire?",
            candidates=candidates,
            top_k=3,
        )

    result_ids = [chunk.id for chunk, _ in results]

    assert result_ids == [2, 1, 3]
    assert results[0][1] == pytest.approx(0.95)


def test_reranker_respects_top_k(candidates):
    with patch("app.retrieval.reranker.get_reranker") as get_model:
        get_model.return_value.compute_score.return_value = [
            0.2, 0.95, 0.1
        ]

        results = rerank_chunks(
            query="When do tokens expire?",
            candidates=candidates,
            top_k=2,
        )

    assert len(results) == 2
    assert [chunk.id for chunk, _ in results] == [2, 1]


def test_reranker_returns_empty_for_no_candidates():
    with patch("app.retrieval.reranker.get_reranker") as get_model:
        results = rerank_chunks(
            query="Any question",
            candidates=[],
        )

    assert results == []
    get_model.assert_not_called()


def test_reranker_rejects_empty_query(candidates):
    with pytest.raises(ValueError, match="query"):
        rerank_chunks(query="  ", candidates=candidates)


def test_reranker_rejects_invalid_top_k(candidates):
    with pytest.raises(ValueError, match="top_k"):
        rerank_chunks(
            query="Any question",
            candidates=candidates,
            top_k=0,
        )
