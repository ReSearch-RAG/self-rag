from unittest.mock import patch

import pytest

from app.db.models.chunk import Chunk
from app.retrieval.retriever import retrieve


@pytest.fixture
def candidates():
    chunk_a = Chunk(id=1, text="Neural networks learn representations")
    chunk_b = Chunk(id=2, text="Hybrid retrieval combines search methods")
    chunk_c = Chunk(id=3, text="Transformers use self-attention")

    return [
        (chunk_a, 0.03),
        (chunk_b, 0.02),
        (chunk_c, 0.01),
    ]


@pytest.fixture
def retrieval_args():
    return {
        "db": object(),
        "query": "hybrid retrieval",
        "query_embedding": [0.1, 0.2, 0.3],
        "document_id": 10,
        "top_k": 2,
        "candidate_k": 10,
    }


def test_retrieve_calls_hybrid_search_with_expected_arguments(
    candidates,
    retrieval_args,
):
    with (
        patch(
            "app.retrieval.retriever.hybrid_search",
            return_value=candidates,
        ) as mock_hybrid,
        patch(
            "app.retrieval.retriever.rerank_chunks",
            return_value=candidates[:2],
        ) as mock_rerank,
    ):
        result = retrieve(**retrieval_args)

    mock_hybrid.assert_called_once_with(
        db=retrieval_args["db"],
        query=retrieval_args["query"],
        query_embedding=retrieval_args["query_embedding"],
        document_id=retrieval_args["document_id"],
        top_k=10,
        candidate_k=10,
    )
    mock_rerank.assert_called_once_with(
        query="hybrid retrieval",
        candidates=candidates,
        top_k=2,
    )
    assert result == candidates[:2]


def test_retrieve_returns_empty_when_no_candidates(retrieval_args):
    with (
        patch(
            "app.retrieval.retriever.hybrid_search",
            return_value=[],
        ) as mock_hybrid,
        patch(
            "app.retrieval.retriever.rerank_chunks",
        ) as mock_rerank,
    ):
        result = retrieve(**retrieval_args)

    assert result == []
    mock_hybrid.assert_called_once()
    mock_rerank.assert_not_called()


@pytest.mark.parametrize(
    "query,top_k,candidate_k,error_message",
    [
        ("", 5, 20, "query must not be empty"),
        ("   ", 5, 20, "query must not be empty"),
        ("valid query", 0, 20, "top_k must be at least 1"),
        ("valid query", 5, 0, "candidate_k must be at least 1"),
    ],
)
def test_retrieve_rejects_invalid_inputs(
    retrieval_args,
    query,
    top_k,
    candidate_k,
    error_message,
):
    retrieval_args.update(
        query=query,
        top_k=top_k,
        candidate_k=candidate_k,
    )

    with pytest.raises(ValueError, match=error_message):
        retrieve(**retrieval_args)


def test_retrieve_preserves_reranker_order(
    candidates,
    retrieval_args,
):
    reranked = [
        (candidates[1][0], 0.95),
        (candidates[2][0], 0.72),
    ]

    with (
        patch(
            "app.retrieval.retriever.hybrid_search",
            return_value=candidates,
        ),
        patch(
            "app.retrieval.retriever.rerank_chunks",
            return_value=reranked,
        ),
    ):
        result = retrieve(**retrieval_args)

    assert [chunk.id for chunk, _ in result] == [2, 3]
    assert [score for _, score in result] == [0.95, 0.72]
