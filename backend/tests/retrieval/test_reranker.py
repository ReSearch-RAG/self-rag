from unittest.mock import MagicMock, patch

import pytest

from app.db.models.chunk import Chunk
from app.retrieval.reranker import get_reranker, rerank_chunks


@pytest.fixture
def candidates():
    chunk_a = Chunk(id=1, text="Information about neural networks")
    chunk_b = Chunk(id=2, text="Information about database indexing")
    chunk_c = Chunk(id=3, text="Information about transformers")

    return [
        (chunk_a, 0.03),
        (chunk_b, 0.02),
        (chunk_c, 0.01),
    ]


def test_rerank_chunks_sorts_by_descending_score(candidates):
    mock_reranker = MagicMock()
    mock_reranker.compute_score.return_value = [0.2, 0.9, 0.5]

    with patch(
        "app.retrieval.reranker.get_reranker",
        return_value=mock_reranker,
    ):
        results = rerank_chunks(
            query="database indexing",
            candidates=candidates,
            top_k=3,
        )

    assert [chunk.id for chunk, _ in results] == [2, 3, 1]
    assert [score for _, score in results] == [0.9, 0.5, 0.2]


def test_rerank_chunks_respects_top_k(candidates):
    mock_reranker = MagicMock()
    mock_reranker.compute_score.return_value = [0.2, 0.9, 0.5]

    with patch(
        "app.retrieval.reranker.get_reranker",
        return_value=mock_reranker,
    ):
        results = rerank_chunks(
            query="database indexing",
            candidates=candidates,
            top_k=2,
        )

    assert len(results) == 2
    assert [chunk.id for chunk, _ in results] == [2, 3]


def test_rerank_chunks_returns_empty_for_no_candidates():
    with patch("app.retrieval.reranker.get_reranker") as mock_get_reranker:
        results = rerank_chunks(
            query="database indexing",
            candidates=[],
        )

    assert results == []
    mock_get_reranker.assert_not_called()


@pytest.mark.parametrize(
    "query,candidates,top_k",
    [
        ("", [], 5),
        ("   ", [], 5),
        ("valid query", [], 0),
    ],
)
def test_rerank_chunks_rejects_invalid_inputs(query, candidates, top_k):
    with pytest.raises(ValueError):
        rerank_chunks(query=query, candidates=candidates, top_k=top_k)


def test_rerank_chunks_rejects_mismatched_score_count(candidates):
    mock_reranker = MagicMock()
    mock_reranker.compute_score.return_value = [0.5]

    with patch(
        "app.retrieval.reranker.get_reranker",
        return_value=mock_reranker,
    ):
        with pytest.raises(
            RuntimeError,
            match="unexpected number of scores",
        ):
            rerank_chunks(
                query="database indexing",
                candidates=candidates,
            )


def test_get_reranker_loads_model_once():
    get_reranker.cache_clear()

    try:
        with patch(
            "app.retrieval.reranker.FlagReranker"
        ) as mock_model_class:
            first = get_reranker()
            second = get_reranker()

            assert first is second
            mock_model_class.assert_called_once_with(
                "BAAI/bge-reranker-v2-m3",
                use_fp16=False,
            )
    finally:
        get_reranker.cache_clear()
