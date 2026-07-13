# Hermes RAG

私人文件問答平台。PDF + Word → Qdrant → MiniMax。

## Stack

- **FastAPI** — backend API
- **Qdrant** — vector DB (embedded mode for dev, server mode for prod)
- **MiniMax** — embeddings + chat (CN Token Plan)
- **Streamlit** — frontend UI
- **PyMuPDF + python-docx** — parsers

## Architecture

```
PDF/Word → Upload (FastAPI)
         → Parse (PyMuPDF / python-docx)
         → Chunk (recursive, 500 char, 50 overlap)
         → Embed (MiniMax embo-01)
         → Qdrant (cosine)

User question → Embed
              → Qdrant top-k=5
              → MiniMax chat (with context)
              → Streamlit UI
```

## Quick start (local)

```bash
cd /opt/data/hermes-rag
cp .env.example .env
# Edit .env: paste your MINIMAX_CN_API_KEY

# Install deps
pip install -r requirements.txt

# Run with docker-compose (Qdrant + API + UI)
docker-compose up

# Or run dev mode
# Terminal 1: Qdrant
docker run -p 6333:6333 qdrant/qdrant:v1.7.4

# Terminal 2: API
uvicorn app.main:app --reload --port 8000

# Terminal 3: UI
streamlit run app/ui.py --server.port 8501
```

UI: http://localhost:8501
API: http://localhost:8000/docs

## Deploy to Zeabur

1. Push to GitHub
2. Zeabur → New Service → Docker
3. Add 2 services:
   - **qdrant** (image: qdrant/qdrant:v1.7.4, persistent volume)
   - **api** (build from Dockerfile, env vars from .env, expose 8000)
4. Streamlit UI: same Dockerfile but different command, expose 8501

## Configuration

All in `.env`:

| Key | Default | Notes |
|-----|---------|-------|
| `MINIMAX_CN_API_KEY` | (required) | Get from minimaxi.com |
| `MINIMAX_CN_BASE_URL` | `https://api.minimaxi.com/v1` | CN endpoint |
| `QDRANT_HOST` | `qdrant` | Service name in docker-compose |
| `QDRANT_PORT` | `6333` | |
| `COLLECTION_NAME` | `docs` | Single collection for now |
| `EMBEDDING_MODEL` | `embo-01` | MiniMax embedding model |
| `CHAT_MODEL` | `MiniMax-Text-01` | MiniMax chat model |
| `CHUNK_SIZE` | `500` | Characters |
| `CHUNK_OVERLAP` | `50` | Characters |
| `TOP_K` | `5` | Retrieval count |

## Phases

- [x] P1 — Backend skeleton (config, MiniMax client, Qdrant wrapper)
- [x] P2 — Ingestion pipeline (parsers, chunker)
- [x] P3 — Chat endpoint (retrieval + LLM)
- [x] P4 — Frontend (Streamlit)
- [ ] P5 — Polish (OCR fallback, re-rank hooks, cost monitor, re-ingest)

## OCR fallback

Stub lives in `app/parsers.py:parse_with_ocr_fallback()`. Wire Mistral OCR when you hit a scanned PDF.

## Re-rank

Stub hook in `app/qa.py:answer()`. Add a cross-encoder reranker step before LLM call when retrieval quality is bad.
