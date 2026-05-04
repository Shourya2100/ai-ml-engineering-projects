from sentence_transformers import CrossEncoder

from app.config import settings
from common.logging import get_logger

logger = get_logger(__name__)


class Reranker:
    """Wraps a cross-encoder model to re-score (query, chunk) pairs."""

    def __init__(self) -> None:
        logger.info("Loading reranker model: %s", settings.RERANKER_MODEL)
        self._model = CrossEncoder(settings.RERANKER_MODEL)
        logger.info("Reranker model loaded")

    def rerank(self, query: str, chunks: list[dict], top_n: int = 3) -> list[dict]:
        """Re-score chunks against the query and return the top_n most relevant."""
        if not chunks:
            return []

        pairs = [(query, chunk["text"]) for chunk in chunks]
        scores = self._model.predict(pairs)

        for i, chunk in enumerate(chunks):
            chunk["rerank_score"] = float(scores[i])

        ranked = sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)
        return ranked[:top_n]
