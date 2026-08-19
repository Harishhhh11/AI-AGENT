"""
Embedding service.

Generates semantic embeddings for knowledge-base
content using the MiniLM sentence-transformer model.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer


EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

EMBEDDING_DIMENSION = 384


class EmbeddingService:
    """
    Generates semantic vector embeddings.
    """

    def __init__(self) -> None:
        self.model = self._load_model()

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_model() -> SentenceTransformer:
        """
        Load the model once and reuse it.
        """

        return SentenceTransformer(
            EMBEDDING_MODEL_NAME
        )

    def generate(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate a 384-dimensional normalized vector.
        """

        if not text or not text.strip():

            raise ValueError(
                "Cannot generate an embedding "
                "from empty text."
            )

        embedding = self.model.encode(
            text.strip(),
            normalize_embeddings=True,
        )

        vector = embedding.tolist()

        if len(vector) != EMBEDDING_DIMENSION:

            raise ValueError(
                "Invalid embedding dimension. "
                f"Expected {EMBEDDING_DIMENSION}, "
                f"got {len(vector)}."
            )

        return vector