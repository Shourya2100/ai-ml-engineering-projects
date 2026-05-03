from datetime import datetime

from chromadb.api.models.Collection import Collection
from sqlalchemy.orm import Session

from app.core.chunker import chunk_document
from app.core.embedder import Embedder
from app.db.sqlite import Document
from app.models.document import DocumentResponse, DocumentStatus
from common.http import bad_request
from common.logging import get_logger

logger = get_logger(__name__)


def index_document(
    filename: str,
    text: str,
    embedder: Embedder,
    collection: Collection,
    session: Session,
) -> DocumentResponse:
    """Run the full ingestion pipeline for a single document.

    Steps: create record -> chunk -> embed -> store in ChromaDB -> update record.
    """
    doc = Document(filename=filename, filepath=filename, status="pending")
    session.add(doc)
    session.flush()

    try:
        chunks = chunk_document(text, filename)

        if not chunks:
            doc.status = "failed"
            session.flush()
            bad_request(f"Document '{filename}' produced no chunks (empty or whitespace-only)")

        embeddings = embedder.embed_batch([c["text"] for c in chunks])

        collection.add(
            ids=[c["chunk_id"] for c in chunks],
            embeddings=embeddings,
            documents=[c["text"] for c in chunks],
            metadatas=[{"filename": c["filename"], "section": c["section"], "chunk_index": c["chunk_index"]} for c in chunks],
        )

        doc.chunk_count = len(chunks)
        doc.status = "indexed"
        doc.indexed_at = datetime.utcnow()
        session.flush()

        logger.info("Indexed '%s': %d chunks", filename, len(chunks))

        return DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            chunk_count=doc.chunk_count,
            status=DocumentStatus(doc.status),
            indexed_at=doc.indexed_at,
        )

    except Exception:
        doc.status = "failed"
        session.flush()
        raise
