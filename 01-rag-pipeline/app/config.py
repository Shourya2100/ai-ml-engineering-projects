import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common.config import load_env, get_env

load_env()


class Settings:
    ANTHROPIC_API_KEY: str = get_env("ANTHROPIC_API_KEY", required=False) or ""
    CHROMA_PATH: str = get_env("CHROMA_PATH", required=False) or "./chroma_db"
    SQLITE_PATH: str = get_env("SQLITE_PATH", required=False) or "./rag.db"
    EMBEDDING_MODEL: str = get_env("EMBEDDING_MODEL", required=False) or "all-MiniLM-L6-v2"
    RERANKER_MODEL: str = get_env("RERANKER_MODEL", required=False) or "cross-encoder/ms-marco-MiniLM-L-6-v2"
    DEFAULT_TOP_K: int = int(get_env("DEFAULT_TOP_K", required=False) or "5")
    LOG_LEVEL: str = get_env("LOG_LEVEL", required=False) or "INFO"


settings = Settings()
