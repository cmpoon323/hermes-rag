# Hermes RAG — Deployment Guide

Single-service deploy: SQLite + numpy for vector store. No external services.

## Option 1: Zeabur dashboard

### 1. Create project
Go to https://zeabur.com → New Project → name it `hermes-rag`

### 2. Add API service (only service)
- Add Service → **Git Repository** → `https://github.com/cmpoon323/hermes-rag.git`
- Service name: `api`
- Port: `8000`
- Health Check: `port-8000` + HTTP path `/health`
- **Environment variables**:
  ```
  MINIMAX_CN_API_KEY=<your_key>
  MINIMAX_CN_BASE_URL=https://api.minimaxi.com/v1
  DB_PATH=./data/rag.db
  COLLECTION_NAME=docs
  EMBEDDING_MODEL=embo-01
  CHAT_MODEL=MiniMax-Text-01
  CHUNK_SIZE=500
  CHUNK_OVERLAP=50
  TOP_K=5
  ```
- **Persistent volume**: mount `/app/data` (2Gi) — preserves both uploads + SQLite db
- Domain: `my-rag.zeabur.app` → port 8000

### 3. Use the API
- API: `https://my-rag.zeabur.app/docs` (Swagger UI)
- Direct API calls work — no separate UI service needed
- If you want a chat UI later, deploy a second service (requires plan upgrade)

---

## Option 2: Local development

```bash
cp .env.example .env
# Edit .env: paste your MINIMAX_CN_API_KEY

docker-compose up
# API: http://localhost:8000/docs
# UI: http://localhost:8501
```

---

## API usage

### Upload
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/doc.pdf"
```
Returns: `{"source": "doc.pdf", "chunks": 12, "vector_size": 1024, "chars": 6234}`

### Ask
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is HIBOR?"}'
```
Returns:
```json
{
  "answer": "...",
  "sources": [
    {"source": "doc.pdf", "chunk_index": 3, "score": 0.87, "preview": "..."}
  ]
}
```

### List documents
```bash
curl http://localhost:8000/documents
```

### Delete document
```bash
curl -X DELETE http://localhost:8000/documents/doc.pdf
```

---

## Architecture

```
PDF/Word → Upload (FastAPI POST /upload)
         → Parse (PyMuPDF / python-docx)
         → Chunk (sentence-aware, 500/50)
         → Embed (MiniMax embo-01, 1024 dim)
         → Save to SQLite (text + vector BLOB)

User question → POST /ask
              → Embed query
              → SQLite scan + numpy cosine similarity
              → Top 5 chunks
              → MiniMax chat completion (with context)
              → Return answer + sources
```

## Resource limits

- 1 service, ~512MB RAM, 1-2GB storage
- Works on Zeabur free tier
- For >5000 docs, consider switching to Qdrant (requires 2-service plan)
