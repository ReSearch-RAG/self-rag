from app.ingestion.embedder import Embedder


def test_embedder():
    embedder = Embedder()

    texts = [
        "PostgreSQL is a relational database.",
        "Vector databases store numerical representations of text.",
    ]

    embeddings = embedder.embed(texts)

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 1024
    assert len(embeddings[1]) == 1024

    print("Number of embeddings:", len(embeddings))
    print("Embedding dimension:", len(embeddings[0]))
    print("First 5 values:", embeddings[0][:5])