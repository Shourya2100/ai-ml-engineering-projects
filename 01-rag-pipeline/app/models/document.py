from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class DocumentStatus(str, Enum):
    pending = "pending"
    indexed = "indexed"
    failed = "failed"


class DocumentResponse(BaseModel):
    id: int
    filename: str
    chunk_count: int
    status: DocumentStatus
    indexed_at: datetime | None = None


class UploadResponse(BaseModel):
    uploaded: int
    documents: list[DocumentResponse]


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


class DeleteResponse(BaseModel):
    deleted: bool
    filename: str
