from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3)
    top_k: int = Field(default=5, ge=1, le=20)


class SourceReference(BaseModel):
    filename: str
    section: str
    score: float


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceReference]
    chunks_retrieved: int
    chunks_after_rerank: int
