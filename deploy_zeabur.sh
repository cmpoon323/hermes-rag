#!/usr/bin/env bash
# Deploy Hermes RAG to Zeabur.
# Usage: ./deploy_zeabur.sh
#
# What this does:
#   1. Verifies zeabur CLI installed
#   2. Verifies .env has MINIMAX_CN_API_KEY
#   3. Initializes Qdrant service (persistent volume)
#   4. Initializes API service (build from Dockerfile)
#   5. Initializes Streamlit UI service
#   6. Sets env vars for cross-service networking
#   7. Triggers first deploy

set -euo pipefail

cd "$(dirname "$0")"

# === Pre-flight checks ===
command -v zeabur >/dev/null 2>&1 || {
  echo "ERROR: zeabur CLI not installed. Install: https://zeabur.com/docs/cli"
  exit 1
}

[ -f .env ] || { echo "ERROR: .env not found. cp .env.example .env first."; exit 1; }
grep -qE '^MINIMAX_CN_API_KEY=.+$' .env || {
  echo "ERROR: MINIMAX_CN_API_KEY empty in .env. Get a key at https://www.minimaxi.com"
  exit 1
}

# === Load env ===
set -a
source .env
set +a

echo "==> Deploying Hermes RAG to Zeabur"
echo "    Project: hermes-rag"
echo "    Services: qdrant, api, ui"
echo

# === 1. Login + create project (idempotent) ===
zeabur auth login --browser 2>/dev/null || zeabur auth status
zeabur project create --name hermes-rag 2>/dev/null || true
zeabur project select hermes-rag

# === 2. Qdrant service ===
echo "==> Creating Qdrant service..."
QDRANT_ID=$(zeabur service create qdrant \
  --name qdrant \
  --image qdrant/qdrant:v1.7.4 \
  --output json | jq -r '.id')
echo "    qdrant service id: $QDRANT_ID"

# Persistent volume for Qdrant storage
zeabur volume create --name qdrant-data --size 5Gi
zeabur volume mount --service "$QDRANT_ID" --volume qdrant-data --path /qdrant/storage

# === 3. API service ===
echo "==> Creating API service..."
API_ID=$(zeabur service create docker \
  --name api \
  --dockerfile ./Dockerfile \
  --output json | jq -r '.id')
echo "    api service id: $API_ID"

# Set MiniMax env vars on API service
zeabur env set --service "$API_ID" \
  MINIMAX_CN_API_KEY="$MINIMAX_CN_API_KEY" \
  MINIMAX_CN_BASE_URL="$MINIMAX_CN_BASE_URL" \
  QDRANT_HOST=qdrant \
  QDRANT_PORT=6333 \
  COLLECTION_NAME=docs \
  EMBEDDING_MODEL=embo-01 \
  CHAT_MODEL=MiniMax-Text-01 \
  CHUNK_SIZE=500 \
  CHUNK_OVERLAP=50 \
  TOP_K=5

# Persistent volume for uploads
zeabur volume create --name api-uploads --size 2Gi
zeabur volume mount --service "$API_ID" --volume api-uploads --path /app/data/uploads

# Expose port 8000
zeabur service port expose --service "$API_ID" --port 8000

# === 4. Streamlit UI service ===
echo "==> Creating UI service..."
UI_ID=$(zeabur service create docker \
  --name ui \
  --dockerfile ./Dockerfile \
  --command "streamlit run app/ui.py --server.port 8501 --server.address 0.0.0.0" \
  --output json | jq -r '.id')
echo "    ui service id: $UI_ID"

# UI needs to know API URL. Get the API's public URL.
API_URL="http://api.zeabur.internal:8000"  # internal DNS within Zeabur
zeabur env set --service "$UI_ID" \
  API_URL="$API_URL" \
  STREAMLIT_SERVER_HEADLESS=true

zeabur service port expose --service "$UI_ID" --port 8501

# === 5. Trigger first deploy ===
echo
echo "==> Triggering first deploy..."
zeabur deploy

echo
echo "✓ Done. Get public URLs:"
echo "    zeabur service list"
echo
echo "Notes:"
echo "  - Qdrant data is persistent (qdrant-data volume, 5Gi)"
echo "  - Uploaded files persist on api-uploads volume"
echo "  - To update code: zeabur deploy"
echo "  - To view logs: zeabur logs --service <name>"
