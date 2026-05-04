import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chromadb

from app.core.embedder import Embedder
from app.core.retriever import retrieve

CHUNKS = [
    {
        "chunk_id": "incident-response.md__chunk_0",
        "text": "When the primary database goes down, the on-call engineer should check the CloudWatch dashboard for error spikes and initiate a failover to the read replica.",
        "filename": "incident-response.md",
        "section": "Database Outage",
        "chunk_index": 0,
    },
    {
        "chunk_id": "refund-policy.md__chunk_0",
        "text": "Digital products are eligible for a full refund within 14 days of purchase if the product has not been downloaded or activated.",
        "filename": "refund-policy.md",
        "section": "Digital Products",
        "chunk_index": 0,
    },
    {
        "chunk_id": "onboarding.md__chunk_0",
        "text": "Welcome to Acme Engineering! On your first day you will receive access to GitHub, Slack, and the internal wiki. Your manager will schedule a 1:1 to go over team norms.",
        "filename": "onboarding.md",
        "section": "Welcome",
        "chunk_index": 0,
    },
]


def _build_test_collection(embedder: Embedder):
    """Create an in-memory ChromaDB collection with test chunks."""
    client = chromadb.Client()
    collection = client.get_or_create_collection(
        name="test_docs",
        metadata={"hnsw:space": "cosine"},
    )
    embeddings = embedder.embed_batch([c["text"] for c in CHUNKS])
    collection.add(
        ids=[c["chunk_id"] for c in CHUNKS],
        embeddings=embeddings,
        documents=[c["text"] for c in CHUNKS],
        metadatas=[{"filename": c["filename"], "section": c["section"], "chunk_index": c["chunk_index"]} for c in CHUNKS],
    )
    return collection


_embedder = None
_collection = None


def _get_fixtures():
    global _embedder, _collection
    if _embedder is None:
        _embedder = Embedder()
        _collection = _build_test_collection(_embedder)
    return _embedder, _collection


def test_retriever_returns_relevant_chunk():
    embedder, collection = _get_fixtures()
    results = retrieve("What do I do when the database goes down?", embedder, collection, top_k=3)
    assert len(results) > 0
    assert results[0]["filename"] == "incident-response.md"


def test_retriever_returns_refund_chunk():
    embedder, collection = _get_fixtures()
    results = retrieve("What is the refund policy for digital products?", embedder, collection, top_k=3)
    assert len(results) > 0
    assert results[0]["filename"] == "refund-policy.md"


def test_retriever_returns_at_most_top_k():
    embedder, collection = _get_fixtures()
    results = retrieve("Tell me about Acme Engineering", embedder, collection, top_k=2)
    assert len(results) <= 2
