# PLAN.md — RAG Pipeline from Scratch
# Project 1 of 4 — ai-ml-engineering-projects monorepo

## Project Overview

A production-shaped RAG (Retrieval Augmented Generation) system that lets users ask
questions about a company's internal documents and get accurate, cited answers. Built
entirely from scratch — no LangChain, no LlamaIndex. Every component is hand-built
so the implementation is fully explainable in interviews.

The system ingests markdown documents, chunks and embeds them, stores them in a vector
database, retrieves relevant chunks using hybrid search (BM25 + vector), reranks results
using a cross-encoder, and generates grounded answers via Claude with citation enforcement.
A minimal single-file chat UI is served directly by FastAPI.

This is Project 1 of a 4-part personal series on AI and ML engineering, all living
in a single monorepo called ai-ml-engineering-projects.

---

## Before You Start

The GitHub repo must already exist and be cloned locally before running this plan.
Steps the developer does manually (not part of this plan):

1. Create a new public repo on GitHub named ai-ml-engineering-projects
2. Clone it: git clone https://github.com/<your-username>/ai-ml-engineering-projects
3. Open the repo root in Cursor
4. Hand this PLAN.md to the agent and say: "Build phase by phase, ask me before
   moving to the next phase."

---

## Monorepo Structure

```
ai-ml-engineering-projects/
├── .gitignore
├── requirements-common.txt
│
├── common/
│   ├── __init__.py
│   ├── config.py
│   ├── logging.py
│   └── http.py
│
└── 01-rag-pipeline/               ← THIS PROJECT
    ├── README.md
    ├── PLAN.md
    ├── requirements.txt
    ├── .env.example
    │
    ├── app/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── config.py
    │   │
    │   ├── api/
    │   │   ├── __init__.py
    │   │   └── routes/
    │   │       ├── __init__.py
    │   │       ├── health.py
    │   │       ├── documents.py
    │   │       └── query.py
    │   │
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── chunker.py
    │   │   ├── embedder.py
    │   │   ├── indexer.py
    │   │   ├── retriever.py
    │   │   ├── reranker.py
    │   │   └── generator.py
    │   │
    │   ├── db/
    │   │   ├── __init__.py
    │   │   ├── chroma.py
    │   │   └── sqlite.py
    │   │
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── document.py
    │   │   └── query.py
    │   │
    │   └── static/
    │       └── index.html
    │
    ├── sample-docs/
    │   ├── engineering/
    │   │   ├── onboarding.md
    │   │   ├── local-dev-setup.md
    │   │   ├── deployment-runbook.md
    │   │   └── incident-response.md
    │   ├── policies/
    │   │   ├── refund-policy.md
    │   │   └── data-retention.md
    │   └── incidents/
    │       ├── march-2025-database-outage.md
    │       └── january-2025-payment-failure.md
    │
    └── tests/
        ├── __init__.py
        ├── test_chunker.py
        ├── test_retriever.py
        └── test_api.py
```

The following folders will be created in future projects. Do NOT create them now:
- 02-llm-eval-harness/
- 03-data-drift-detective/
- 04-feature-store/

---

## Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Runtime |
| FastAPI | 0.111+ | REST API + serves chat UI |
| Uvicorn | 0.29+ | ASGI server |
| Anthropic SDK | 0.25+ | Claude API for generation |
| sentence-transformers | 2.7+ | Embed chunks and queries |
| chromadb | 0.5+ | Vector database for semantic search |
| rank-bm25 | 0.2+ | BM25 keyword search |
| tiktoken | 0.7+ | Measure chunk sizes in tokens |
| SQLAlchemy | 2.x | ORM for SQLite |
| Pydantic | 2.x | Request and response validation |
| Pytest | 8.x | Unit tests |
| httpx | 0.27+ | Async HTTP client for tests |

---

## Databases

Two databases serve different purposes:

ChromaDB (vector database)
- Stores chunk text + embeddings + metadata
- Used for semantic similarity search
- Persisted to disk at ./chroma_db/

SQLite via SQLAlchemy (relational database)
- Stores document records (filename, upload time, chunk count, status)
- Stores query history (question, answer, sources, timestamp)
- Used for document management and audit trail
- Persisted to disk at ./rag.db

---

## API Design

### GET /health
Returns server status.
Response: { "status": "ok", "project": "rag-pipeline" }

### POST /documents/upload
Upload one or more markdown files for indexing.
Request: multipart/form-data, files: list[UploadFile]
Response:
{
  "uploaded": 3,
  "documents": [
    { "id": 1, "filename": "incident-response.md", "chunks": 8, "status": "indexed" }
  ]
}

### GET /documents
List all indexed documents.
Response: { "documents": [ { "id", "filename", "chunks", "indexed_at" } ] }

### DELETE /documents/{document_id}
Remove a document and all its chunks from the index.
Response: { "deleted": true, "filename": "incident-response.md" }

### POST /ask
Ask a question. Returns an answer with cited sources.
Request: { "question": "What do I do when the database goes down?", "top_k": 5 }
Response:
{
  "question": "What do I do when the database goes down?",
  "answer": "According to the incident response runbook, you should first
             check the CloudWatch dashboard for error spikes...",
  "sources": [
    { "filename": "incident-response.md", "section": "Database Outage", "score": 0.94 }
  ],
  "chunks_retrieved": 5,
  "chunks_after_rerank": 3
}

### GET / (root)
Serves the chat UI (index.html).

---

## Core Concepts Per Module

### app/core/chunker.py
Splits a document into overlapping chunks of fixed token size.
- Chunk size: 400 tokens
- Overlap: 50 tokens
- Tokeniser: tiktoken cl100k_base
- Each chunk carries: text, source filename, section heading, chunk index

### app/core/embedder.py
Converts text into a vector of 384 numbers.
- Model: sentence-transformers all-MiniLM-L6-v2
- Model loaded once at startup, reused for all chunks and queries
- Same model used for both indexing and querying (critical rule)

### app/core/indexer.py
Orchestrates the full ingestion pipeline for a document.
Calls: chunker → embedder → chroma (store) → sqlite (record)

### app/core/retriever.py
Hybrid retrieval combining semantic search and keyword search.
- Semantic: ChromaDB cosine similarity search (top_k * 2 candidates)
- Keyword: BM25 over the same candidate pool
- Fusion: Reciprocal Rank Fusion (RRF) to merge both ranked lists
- Returns merged, deduplicated list of top_k chunks

### app/core/reranker.py
Re-scores retrieved chunks using a cross-encoder model.
- Model: cross-encoder/ms-marco-MiniLM-L-6-v2 (free, runs locally)
- Takes (query, chunk) pairs and produces a relevance score
- Returns chunks sorted by reranker score, keeps top 3

### app/core/generator.py
Assembles the final prompt and calls Claude.
- Builds a prompt with: system instruction, retrieved chunks as context,
  user question, citation instruction
- Claude must answer only from provided context
- Claude must cite the source filename in its answer
- Returns answer text and source list extracted from response

---

## Sample Documents

Create these mock company documents with realistic content.
They should be 300-500 words each to produce multiple chunks.
Write them as real internal docs for a fictional company called Acme Engineering.

### engineering/incident-response.md
Sections: Database Outage, Payment Service Failure, Network Partitions,
On-call Rotation, Escalation Policy

### engineering/local-dev-setup.md
Sections: Prerequisites, Cloning the Repo, Environment Variables,
Running Services Locally, Common Setup Issues, Testing Your Setup

### engineering/deployment-runbook.md
Sections: Pre-deployment Checklist, Deployment Steps, Rollback Procedure,
Post-deployment Verification, Hotfix Process

### engineering/onboarding.md
Sections: Welcome, Tools and Access, First Week Checklist,
Team Structure, Communication Channels, Getting Help

### policies/refund-policy.md
Sections: Digital Products, Physical Products, Subscription Cancellations,
Exceptions, How to Request a Refund, Processing Times

### policies/data-retention.md
Sections: Customer Data, Log Retention, Backup Policy,
GDPR Compliance, Data Deletion Requests

### incidents/march-2025-database-outage.md
A realistic post-incident report. Sections: Summary, Timeline,
Root Cause, Impact, Resolution, Action Items

### incidents/january-2025-payment-failure.md
A realistic post-incident report. Sections: Summary, Timeline,
Root Cause, Impact, Resolution, Action Items

---

## Chat UI (index.html)

A single HTML file served by FastAPI at the root route.
No React, no build step, no external CSS framework.
Vanilla HTML + CSS + JavaScript only.

Layout:
- Header: "Acme Engineering Assistant" with a subtitle
- Chat area: message history, user messages right-aligned,
  assistant messages left-aligned
- Source pills below each assistant message showing cited filenames
- Input bar at bottom: text field + Send button
- Loading indicator while waiting for response

The UI calls POST /ask and renders the answer and sources.
Clean and screenshot-ready for LinkedIn.

---

## Implementation Phases

Work through these in order. Each phase = one Git branch + one commit.
Ask the developer before moving to the next phase.

---

### Phase 1 — Monorepo Scaffold
**Branch:** phase/1-monorepo-scaffold

At the repo root:
- [ ] Create .gitignore covering: __pycache__/, *.pyc, .env, venv/, .venv/,
      chroma_db/, *.db, .DS_Store, *.egg-info/
- [ ] Create requirements-common.txt:
      fastapi, uvicorn[standard], pydantic, anthropic, python-dotenv
- [ ] Create common/__init__.py (empty)
- [ ] Create common/config.py
      - load_env() loads .env from repo root via python-dotenv
      - get_env(key, required=True) raises ValueError if required and missing
- [ ] Create common/logging.py
      - get_logger(name) returns a configured Logger
      - Format: %(asctime)s | %(name)s | %(levelname)s | %(message)s
      - Level from LOG_LEVEL env var, default INFO
- [ ] Create common/http.py
      - bad_request(detail) raises HTTPException(400)
      - not_found(detail) raises HTTPException(404)
      - server_error(detail) raises HTTPException(500)

Inside 01-rag-pipeline/:
- [ ] Create .env.example:
      ANTHROPIC_API_KEY=your_key_here
      CHROMA_PATH=./chroma_db
      SQLITE_PATH=./rag.db
      EMBEDDING_MODEL=all-MiniLM-L6-v2
      RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
      DEFAULT_TOP_K=5
      LOG_LEVEL=INFO
- [ ] Create requirements.txt:
      sentence-transformers, chromadb, rank-bm25, tiktoken,
      sqlalchemy, httpx, pytest, pytest-asyncio
- [ ] Create app/__init__.py
- [ ] Create app/config.py
      Calls load_env() from common.config
      Exposes all env vars from .env.example with sensible defaults
- [ ] Create app/main.py
      FastAPI app titled "RAG Pipeline"
      Registers all routers
      Serves static/index.html at GET /
      CORS middleware, allow all origins
      Lifespan context manager that initialises Embedder, Reranker,
      ChromaDB collection, and SQLite tables at startup
- [ ] Create app/api/__init__.py and app/api/routes/__init__.py
- [ ] Create app/api/routes/health.py
      GET /health returns {"status": "ok", "project": "rag-pipeline"}

Done when: uvicorn app.main:app --reload starts from inside 01-rag-pipeline/
and curl localhost:8000/health returns 200.

---

### Phase 2 — Database Setup
**Branch:** phase/2-database-setup

- [ ] Create app/db/__init__.py
- [ ] Create app/db/sqlite.py
      SQLAlchemy setup with two tables:

      Document table:
        id: int primary key autoincrement
        filename: str unique not null
        filepath: str not null
        chunk_count: int default 0
        status: str default "pending"  (pending | indexed | failed)
        indexed_at: datetime nullable
        created_at: datetime default now

      QueryLog table:
        id: int primary key autoincrement
        question: str not null
        answer: str not null
        sources: str not null  (JSON string of source list)
        chunks_retrieved: int
        chunks_after_rerank: int
        created_at: datetime default now

      Functions to expose:
        get_session() context manager returning SQLAlchemy session
        create_tables() creates all tables if they do not exist
        Called once at app startup via lifespan event in main.py

- [ ] Create app/db/chroma.py
      get_collection() returns the ChromaDB collection
        client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
        collection = client.get_or_create_collection(
          name="company_docs",
          metadata={"hnsw:space": "cosine"}
        )
      Called once at startup, reused across requests

Done when: Tables are created on startup and ChromaDB collection
initialises without errors.

---

### Phase 3 — Pydantic Models
**Branch:** phase/3-models

- [ ] Create app/models/__init__.py
- [ ] Create app/models/document.py
      DocumentStatus: Enum (pending, indexed, failed)
      DocumentResponse: id, filename, chunk_count, status, indexed_at
      UploadResponse: uploaded count, list of DocumentResponse
      DocumentListResponse: list of DocumentResponse
      DeleteResponse: deleted bool, filename

- [ ] Create app/models/query.py
      AskRequest: question (str, min 3 chars), top_k (int, default 5, max 20)
      SourceReference: filename, section, score (float)
      AskResponse: question, answer, sources list, chunks_retrieved,
                   chunks_after_rerank

Done when: All models import and instantiate without errors.

---

### Phase 4 — Core: Chunker and Embedder
**Branch:** phase/4-chunker-embedder

This phase implements the Phase 1 and Phase 2 ML concepts.
Verify each module manually before moving on.

- [ ] Create app/core/__init__.py
- [ ] Create app/core/chunker.py
      from common.logging import get_logger

      chunk_document(text: str, filename: str, chunk_size: int = 400,
                     overlap: int = 50) -> list[dict]

      Implementation:
        - Load tiktoken encoder: tiktoken.get_encoding("cl100k_base")
        - Tokenise the full text
        - Detect section headings (lines starting with ##) to track
          current section heading as chunks are created
        - Slide a window of chunk_size tokens with overlap tokens of overlap
        - For each window, decode tokens back to text
        - Build chunk dict:
          {
            "text": decoded chunk text,
            "filename": filename,
            "section": current section heading or "General",
            "chunk_index": integer index,
            "chunk_id": f"{filename}__chunk_{index}"
          }
        - Return list of chunk dicts

      Edge cases:
        - Document shorter than chunk_size: return as single chunk
        - Empty document: return empty list
        - Log chunk count at INFO level

- [ ] Create app/core/embedder.py
      from sentence_transformers import SentenceTransformer

      Class Embedder:
        __init__: loads model from settings.EMBEDDING_MODEL
        embed(text: str) -> list[float]
        embed_batch(texts: list[str]) -> list[list[float]]

      Instantiated once at startup via lifespan, stored on app.state.embedder
      Do NOT reload model on each request

- [ ] Create tests/test_chunker.py
      - Document with two sections produces correct chunk count
      - Overlap text appears at start of second chunk
      - Document shorter than chunk_size returns exactly one chunk
      - Empty document returns empty list
      - chunk_id format matches filename__chunk_N

Done when: pytest tests/test_chunker.py passes and embed() returns
a list of 384 floats.

---

### Phase 5 — Core: Indexer and Document API
**Branch:** phase/5-indexer-documents-api

- [ ] Create app/core/indexer.py
      index_document(filename, text, embedder, collection, session)
        -> DocumentResponse

      Steps:
        1. Create Document record in SQLite with status "pending"
        2. chunker.chunk_document(text, filename)
        3. If no chunks: update status "failed", raise bad_request
        4. embedder.embed_batch([c["text"] for c in chunks])
        5. collection.add(ids, embeddings, documents, metadatas)
        6. Update SQLite: chunk_count, status "indexed", indexed_at = now
        7. Return DocumentResponse
        8. On exception: update status "failed", re-raise

- [ ] Create app/api/routes/documents.py
      POST /documents/upload
        - Accept files: list[UploadFile]
        - Allow .md and .txt only, reject others with bad_request
        - For each file: decode utf-8, call indexer.index_document
        - Return UploadResponse

      GET /documents
        - Query SQLite for all Document records
        - Return DocumentListResponse

      DELETE /documents/{document_id}
        - Look up Document in SQLite, 404 if not found
        - collection.delete(where={"filename": document.filename})
        - Delete SQLite record
        - Return DeleteResponse

Done when: Full document lifecycle works via curl — upload, list, delete.

---

### Phase 6 — Core: Retriever and Reranker
**Branch:** phase/6-retriever-reranker

STOP before building this phase. Read the Phase 3 concept explanation
(BM25, hybrid retrieval, reranking) with Claude before writing any code.

- [ ] Create app/core/retriever.py
      retrieve(query, embedder, collection, top_k=5) -> list[dict]

      Step 1 — Semantic search:
        query_vector = embedder.embed(query)
        results = collection.query(
          query_embeddings=[query_vector],
          n_results=top_k * 2,
          include=["documents", "metadatas", "distances"]
        )
        semantic_score = 1 - distance for each result

      Step 2 — BM25 over semantic candidate pool:
        corpus = [chunk["text"] for chunk in candidates]
        tokenised = [text.lower().split() for text in corpus]
        bm25 = BM25Okapi(tokenised)
        bm25_scores = bm25.get_scores(query.lower().split())

      Step 3 — Reciprocal Rank Fusion:
        rrf_score = 1/(semantic_rank + 60) + 1/(bm25_rank + 60)
        Sort by rrf_score descending, deduplicate, return top_k

- [ ] Create app/core/reranker.py
      Class Reranker:
        __init__: CrossEncoder(settings.RERANKER_MODEL)
        rerank(query, chunks, top_n=3) -> list[dict]
          pairs = [(query, chunk["text"]) for chunk in chunks]
          scores = model.predict(pairs)
          sort by score descending, return top_n

      Instantiated once at startup via lifespan, stored on app.state.reranker

- [ ] Create tests/test_retriever.py
      Index 3 chunks into a test ChromaDB collection
      Query with a relevant question
      Assert top result matches the expected chunk

Done when: retrieve() + reranker.rerank() returns correctly ordered
chunks on a small test set.

---

### Phase 7 — Core: Generator and Query API
**Branch:** phase/7-generator-query-api

STOP before building this phase. Read the Phase 4 concept explanation
(prompt templates, context windows, citation enforcement) with Claude.

- [ ] Create app/core/generator.py
      SYSTEM_PROMPT instructs Claude to:
        - Answer ONLY from provided context
        - Say "I could not find information about this" if not in context
        - End every answer with: Sources: [filename1.md, filename2.md]
        - Never hallucinate or use outside knowledge

      generate(query: str, chunks: list[dict]) -> dict
        1. Build context block from chunks with filename/section headers
        2. Call Claude claude-3-5-haiku-20241022, max_tokens=1000
        3. Parse "Sources: [...]" line from end of response
        4. Strip Sources line from displayed answer
        5. Match filenames to chunk metadata for SourceReference list
        6. Retry once on anthropic.APIError, then server_error()
        7. Return {"answer": clean_answer, "sources": source_references}

- [ ] Create app/api/routes/query.py
      POST /ask
        1. Validate AskRequest
        2. retriever.retrieve(question, embedder, collection, top_k)
        3. If no chunks: return "No relevant documents found."
        4. reranker.rerank(question, chunks, top_n=3)
        5. generator.generate(question, reranked_chunks)
        6. Log QueryLog to SQLite
        7. Return AskResponse

Done when: POST /ask returns a correct cited answer for questions
about the sample docs.

---

### Phase 8 — Chat UI
**Branch:** phase/8-chat-ui

- [ ] Create app/static/index.html
      Single file. Vanilla HTML + CSS + JavaScript. No frameworks, no CDN.

      Layout:
        Header: "Acme Engineering Assistant"
        Chat area: scrollable message history
          User messages: right-aligned, teal background
          Assistant messages: left-aligned, gray background
          Source pills below assistant messages (small rounded tags)
        Input bar pinned to bottom: text input + Send button
        Loading state: "Thinking..." while awaiting response
        Enter key submits

      On send:
        1. Append user message to chat
        2. Show loading
        3. POST /ask with {question, top_k: 5}
        4. Append assistant message + source pills
        5. Scroll to bottom
        6. Re-enable input

      Styling: clean, minimal, screenshot-ready for LinkedIn.

Done when: Full conversation works in the browser at localhost:8000.

---

### Phase 9 — Sample Docs and README
**Branch:** phase/9-sample-docs-readme

- [ ] Write all 8 sample markdown documents listed in Sample Documents.
      Each must be 300-500 words with realistic Acme Engineering content.

- [ ] Write 01-rag-pipeline/README.md
      - What it does (1 paragraph)
      - Why no LangChain (1 paragraph — the key differentiator)
      - Quick start (clone → install → env → run → upload → ask)
      - Tech stack table
      - API reference (one line per endpoint)

Done when: A new developer can clone and run in under 5 minutes.

---

## Error Handling Rules

- Invalid file type → HTTP 400 via bad_request()
- Document not found → HTTP 404 via not_found()
- Claude API failure after one retry → HTTP 502 via server_error()
- No chunks indexed when query arrives → graceful "no documents" answer
- All unexpected errors → HTTP 500 via server_error()
- Never expose raw tracebacks to the client
- Use get_logger() everywhere — no bare print() statements

---

## Environment Variables

```
ANTHROPIC_API_KEY=<your key>                         # Required
CHROMA_PATH=./chroma_db                              # Optional
SQLITE_PATH=./rag.db                                 # Optional
EMBEDDING_MODEL=all-MiniLM-L6-v2                    # Optional
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2 # Optional
DEFAULT_TOP_K=5                                      # Optional
LOG_LEVEL=INFO                                       # Optional
```

---

## Important Notes for the Agent

1. Embedder and Reranker must load ONCE at startup via FastAPI lifespan,
   stored on app.state. Never instantiate inside route handlers.

2. ChromaDB collection and SQLAlchemy session factory must also init
   at startup via lifespan, not per request.

3. chunk_id format must be stable: f"{filename}__{chunk_index}"
   This enables targeted deletion when a document is removed.

4. When deleting a document, remove from BOTH ChromaDB and SQLite.

5. BM25 is built fresh per query over the semantic candidate pool only.
   It is NOT pre-built over the full corpus. This avoids stale index
   issues and keeps the implementation simple for MVP.

6. Keep top_k * 2 candidates at a maximum of 20 to keep reranking
   latency under 2 seconds on a laptop CPU.

7. Strip the "Sources: [...]" line from the answer before returning
   to the user — this line is for parsing only, not for display.

---

## What Is NOT In Scope

- No authentication on endpoints
- No async LLM calls — synchronous is fine
- No document re-indexing — delete and re-upload to update
- No PDF or DOCX support — markdown and txt only
- No streaming LLM responses
- No Docker or containerisation
- No CLAUDE.md or .cursorrules — planned after this project ships
- No root README.md for the monorepo — planned after this project
- No other project folders (02, 03, 04)

---

## Definition of Done

1. POST /documents/upload indexes all 8 sample docs without errors
2. POST /ask returns correct cited answers for:
   - "What do I do when the database goes down?"
   - "How do I set up my local dev environment?"
   - "What is the refund policy for digital products?"
   - "What caused the March 2025 database outage?"
3. GET /documents lists all docs with correct chunk counts
4. DELETE /documents/{id} removes a doc and its chunks cleanly
5. Chat UI loads at localhost:8000 and a full conversation works
6. All tests pass: pytest 01-rag-pipeline/tests/
7. README complete and runnable in under 5 minutes
8. One meaningful commit per phase pushed to personal GitHub
