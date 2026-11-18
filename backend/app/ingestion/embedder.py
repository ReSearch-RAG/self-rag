import logging
import math
from functools import lru_cache

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

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


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """Load BGE-M3 once and reuse it across the entire application."""
    logger.info("Loading embedding model %s", MODEL_NAME)
    return Embedder()