# Hermes RAG — Deployment Guide

## Option 1: Zeabur dashboard (recommended for first deploy)

### 1. Create project
Go to https://zeabur.com → New Project → name it `hermes-rag`

### 2. Add Qdrant service
- Add Service → Marketplace → search "Qdrant" → Add
- Or: Add Service → Docker Image → `qdrant/qdrant:v1.7.4`
- Persistent volume: Settings → Volumes → Add → mount `/qdrant/storage` (5Gi)
- Note its service name (default: `qdrant`)

### 3. Add API service
- Add Service → Git → select this repo (or Docker → Dockerfile)
- Dockerfile path: `./Dockerfile`
- Expose port: `8000`
- Set environment variables:
  ```
  MINIMAX_CN_API_KEY=<your_key>
  MINIMAX_CN_BASE_URL=https://api.minimaxi.com/v1
  QDRANT_HOST=qdrant
  QDRANT_PORT=6333
  COLLECTION_NAME=docs
  EMBEDDING_MODEL=embo-01
  CHAT_MODEL=MiniMax-Text-01
  CHUNK_SIZE=500
  CHUNK_OVERLAP=50
  TOP_K=5
  ```
- Persistent volume: mount `/app/data/uploads` (2Gi)
- Domain: add public domain (e.g. `rag-api.your-domain.com`)

### 4. Add UI service
- Add Service → Git → same repo
- Custom command: `streamlit run app/ui.py --server.port 8501 --server.address 0.0.0.0`
- Expose port: `8501`
- Set environment variables:
  ```
  API_URL=http://api.zeabur.internal:8000
  STREAMLIT_SERVER_HEADLESS=true
  ```
  Replace `api.zeabur.internal` with your API service name. Or if you want the public URL:
  ```
  API_URL=https://rag-api.your-domain.com
  ```
- Domain: add public domain (e.g. `rag.your-domain.com`)

### 5. Verify
- Open `https://rag.your-domain.com` → should see Streamlit UI
- Upload a test PDF
- Check API logs if anything fails: Service → API → Logs

---

## Option 2: zeabur CLI (faster for repeat deploys)

```bash
# Install
curl -fsSL https://zeabur.com/install.sh | bash

# Login
zeabur auth login

# From this project dir
./deploy_zeabur.sh

# Update code later
zeabur deploy
```

---

## Option 3: Local development with Docker

```bash
cp .env.example .env
# Edit .env: paste your MINIMAX_CN_API_KEY
# Change QDRANT_HOST=embedded to QDRANT_HOST=qdrant

docker-compose up
```

UI: http://localhost:8501
API docs: http://localhost:8000/docs

---

## Resource sizing (Zeabur)

| Service | RAM | Storage | Notes |
|---------|-----|---------|-------|
| qdrant | 512MB | 5Gi | Scales with vector count. 5Gi ≈ 5M vectors |
| api | 512MB | 2Gi | For uploads |
| ui | 256MB | 0 | Streamlit is light |

Total: ~1.3GB RAM, 7Gi storage. Fits free tier if Zeabur has one; otherwise ~$5/mo.

---

## Persistent data layout

```
api service volume (api-uploads, 2Gi)
  /app/data/uploads/  ← user-uploaded files (preserved)

qdrant service volume (qdrant-data, 5Gi)
  /qdrant/storage/    ← vector index + payloads (preserved)

# If you ever need to wipe & restart:
# 1. Delete both volumes in Zeabur dashboard
# 2. Re-deploy
# Note: deleting qdrant-data loses all ingested vectors — must re-upload
```
