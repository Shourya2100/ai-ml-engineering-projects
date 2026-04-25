import chromadb
from chromadb.api.models.Collection import Collection

from app.config import settings
from common.logging import get_logger

logger = get_logger(__name__)

_client: chromadb.ClientAPI | None = None
_collection: Collection | None = None

COLLECTION_NAME = "company_docs"


def get_collection() -> Collection:
    """Return the persistent ChromaDB collection, creating it on first call."""
    global _client, _collection

    if _collection is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB collection '%s' ready at %s (count=%d)",
            COLLECTION_NAME,
            settings.CHROMA_PATH,
            _collection.count(),
        )

    return _collection
