from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-m3"


class Embedder:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        self.tokenizer = self.model.tokenizer

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
        )

        return embeddings.tolist()

    def count_tokens(self, text: str) -> int:
        tokens = self.tokenizer.encode(
            text,
            add_special_tokens=False,
        )
        return len(tokens)