# Hermes RAG

私人文件問答平台。PDF + Word → SQLite (with numpy) → MiniMax。

## Stack

- **FastAPI** — backend API
- **SQLite + numpy** — vector store (in-process, no external service)
- **MiniMax** — embeddings + chat (CN Token Plan)
- **Streamlit** — optional frontend UI
- **PyMuPDF + python-docx** — parsers

## Architecture

```
PDF/Word → Upload (FastAPI)
         → Parse (PyMuPDF / python-docx)
         → Chunk (recursive, 500 char, 50 overlap)
         → Embed (MiniMax embo-01, 1024 dim)
         → Save to SQLite (text + vector BLOB)

User question → Embed
              → SQLite scan + numpy cosine similarity
              → Top 5 chunks
              → MiniMax chat (with context)
              → Streamlit UI
```

## Single service, no Qdrant

Vector store lives inside the same process as the API. One service, one volume, one deployment. Works on free Zeabur tier.

For >5000 documents, switch to Qdrant (requires 2-service plan).

## Quick start (local)

```bash
cp .env.example .env
# Edit .env: paste your MINIMAX_CN_API_KEY

docker-compose up
```

API: http://localhost:8000/docs

## Deploy to Zeabur

See [DEPLOY.md](DEPLOY.md).

## Configuration

| Key | Default | Notes |
|-----|---------|-------|
| `MINIMAX_CN_API_KEY` | (required) | Get from minimaxi.com |
| `MINIMAX_CN_BASE_URL` | `https://api.minimaxi.com/v1` | CN endpoint |
| `DB_PATH` | `./data/rag.db` | SQLite file path |
| `EMBEDDING_MODEL` | `embo-01` | MiniMax embedding model |
| `CHAT_MODEL` | `MiniMax-Text-01` | MiniMax chat model |
| `CHUNK_SIZE` | `500` | Characters |
| `CHUNK_OVERLAP` | `50` | Characters |
| `TOP_K` | `5` | Retrieval count |
