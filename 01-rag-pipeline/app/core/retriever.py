from rank_bm25 import BM25Okapi
from chromadb.api.models.Collection import Collection

from app.core.embedder import Embedder
from common.logging import get_logger

logger = get_logger(__name__)


def retrieve(
    query: str,
    embedder: Embedder,
    collection: Collection,
    top_k: int = 5,
) -> list[dict]:
    """Hybrid retrieval: semantic search + BM25 keyword search, fused with RRF."""

    candidate_count = min(top_k * 2, 20)

    # Step 1 — Semantic search via ChromaDB
    query_vector = embedder.embed(query)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=candidate_count,
        include=["documents", "metadatas", "distances"],
    )

    if not results["ids"] or not results["ids"][0]:
        logger.info("No chunks found for query: %s", query[:80])
        return []

    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    candidates = []
    for i, chunk_id in enumerate(ids):
        candidates.append({
            "chunk_id": chunk_id,
            "text": documents[i],
            "filename": metadatas[i]["filename"],
            "section": metadatas[i]["section"],
            "chunk_index": metadatas[i]["chunk_index"],
            "semantic_score": 1 - distances[i],
        })

    # Step 2 — BM25 over the semantic candidate pool
    corpus = [c["text"] for c in candidates]
    tokenised = [text.lower().split() for text in corpus]
    bm25 = BM25Okapi(tokenised)
    bm25_scores = bm25.get_scores(query.lower().split())

    # Assign BM25 ranks (higher score = lower/better rank)
    bm25_ranked = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)
    bm25_rank_map = {idx: rank for rank, idx in enumerate(bm25_ranked)}

    # Assign semantic ranks (candidates are already sorted by distance from ChromaDB)
    semantic_rank_map = {i: i for i in range(len(candidates))}

    # Step 3 — Reciprocal Rank Fusion
    k = 60
    for i, candidate in enumerate(candidates):
        sem_rank = semantic_rank_map[i]
        bm25_rank = bm25_rank_map[i]
        candidate["rrf_score"] = 1 / (sem_rank + k) + 1 / (bm25_rank + k)

    # Sort by RRF score descending, deduplicate, return top_k
    candidates.sort(key=lambda c: c["rrf_score"], reverse=True)
    seen = set()
    deduped = []
    for c in candidates:
        if c["chunk_id"] not in seen:
            seen.add(c["chunk_id"])
            deduped.append(c)

    result = deduped[:top_k]
    logger.info(
        "Retrieved %d chunks for query (from %d candidates): %s",
        len(result), len(candidates), query[:80],
    )
    return result
