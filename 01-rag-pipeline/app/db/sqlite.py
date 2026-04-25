from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings
from common.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, unique=True, nullable=False)
    filepath = Column(String, nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    status = Column(String, default="pending", nullable=False)
    indexed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    sources = Column(String, nullable=False)
    chunks_retrieved = Column(Integer, nullable=False)
    chunks_after_rerank = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


_engine = create_engine(f"sqlite:///{settings.SQLITE_PATH}", echo=False, future=True)
_SessionFactory = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def get_session() -> Iterator[Session]:
    """Yield a SQLAlchemy session, committing on success and rolling back on error."""
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables() -> None:
    """Create all tables if they do not already exist. Safe to call multiple times."""
    Base.metadata.create_all(_engine)
    logger.info("SQLite tables ready at %s", settings.SQLITE_PATH)
