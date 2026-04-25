from sentence_transformers import SentenceTransformer

from app.config import settings
from common.logging import get_logger

logger = get_logger(__name__)


class Embedder:
    """Wraps a sentence-transformers model for single and batch embedding."""

    def __init__(self) -> None:
        logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
        self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded (dim=%d)", self._model.get_embedding_dimension())

    def embed(self, text: str) -> list[float]:
        """Embed a single text string into a vector."""
        return self._model.encode(text, convert_to_numpy=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts into a list of vectors."""
        return self._model.encode(texts, convert_to_numpy=True).tolist()
