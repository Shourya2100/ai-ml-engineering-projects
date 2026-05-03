from fastapi import APIRouter, Request, UploadFile

from app.core.indexer import index_document
from app.db.sqlite import Document, get_session
from app.models.document import (
    DeleteResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentStatus,
    UploadResponse,
)
from common.http import bad_request, not_found
from common.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".md", ".txt"}


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(request: Request, files: list[UploadFile]):
    embedder = request.app.state.embedder
    collection = request.app.state.chroma_collection
    results: list[DocumentResponse] = []

    for file in files:
        ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            bad_request(f"Unsupported file type '{ext}'. Only .md and .txt files are allowed.")

        content = (await file.read()).decode("utf-8")

        with get_session() as session:
            existing = session.query(Document).filter(Document.filename == file.filename).first()
            if existing:
                bad_request(f"Document '{file.filename}' already exists. Delete it first to re-upload.")

            doc_response = index_document(
                filename=file.filename,
                text=content,
                embedder=embedder,
                collection=collection,
                session=session,
            )
            results.append(doc_response)

    return UploadResponse(uploaded=len(results), documents=results)


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    with get_session() as session:
        docs = session.query(Document).all()
        return DocumentListResponse(
            documents=[
                DocumentResponse(
                    id=doc.id,
                    filename=doc.filename,
                    chunk_count=doc.chunk_count,
                    status=DocumentStatus(doc.status),
                    indexed_at=doc.indexed_at,
                )
                for doc in docs
            ]
        )


@router.delete("/{document_id}", response_model=DeleteResponse)
async def delete_document(request: Request, document_id: int):
    collection = request.app.state.chroma_collection

    with get_session() as session:
        doc = session.query(Document).filter(Document.id == document_id).first()
        if not doc:
            not_found(f"Document with id {document_id} not found")

        collection.delete(where={"filename": doc.filename})
        filename = doc.filename
        session.delete(doc)

    logger.info("Deleted document '%s' (id=%d)", filename, document_id)
    return DeleteResponse(deleted=True, filename=filename)
