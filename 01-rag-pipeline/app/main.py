import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from common.logging import get_logger
from app.api.routes.health import router as health_router
from app.db.chroma import get_collection
from app.db.sqlite import create_tables

logger = get_logger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RAG Pipeline...")
    create_tables()
    app.state.chroma_collection = get_collection()
    # Embedder and Reranker will be initialised here in later phases
    yield
    logger.info("Shutting down RAG Pipeline.")


app = FastAPI(title="RAG Pipeline", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)


@app.get("/")
async def root():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Chat UI not yet available. Visit /health to verify the server is running."}
