#!/usr/bin/env bash
# Deploy Hermes RAG (single-service) to Zeabur.
# Usage: ./deploy_zeabur.sh
#
# Single service: FastAPI + SQLite (no Qdrant needed).

set -euo pipefail

cd "$(dirname "$0")"

command -v zeabur >/dev/null 2>&1 || {
  echo "ERROR: zeabur CLI not installed. Install: https://zeabur.com/docs/cli"
  exit 1
}

[ -f .env ] || { echo "ERROR: .env not found. cp .env.example .env first."; exit 1; }
grep -qE '^MINIMAX_CN_API_KEY=.+$' .env || {
  echo "ERROR: MINIMAX_CN_API_KEY empty in .env. Get a key at https://www.minimaxi.com"
  exit 1
}

set -a; source .env; set +a

echo "==> Deploying Hermes RAG to Zeabur (single service)"
echo "    Project: hermes-rag"
echo

zeabur auth login --browser 2>/dev/null || zeabur auth status
zeabur project create --name hermes-rag 2>/dev/null || true
zeabur project select hermes-rag

echo "==> Creating API service..."
API_ID=$(zeabur service create docker \
  --name api \
  --dockerfile ./Dockerfile \
  --output json | jq -r '.id')
echo "    api service id: $API_ID"

zeabur env set --service "$API_ID" \
  MINIMAX_CN_API_KEY="$MINIMAX_CN_API_KEY" \
  MINIMAX_CN_BASE_URL="$MINIMAX_CN_BASE_URL" \
  DB_PATH=./data/rag.db \
  COLLECTION_NAME=docs \
  EMBEDDING_MODEL=embo-01 \
  CHAT_MODEL=MiniMax-Text-01 \
  CHUNK_SIZE=500 \
  CHUNK_OVERLAP=50 \
  TOP_K=5

zeabur volume create --name api-data --size 2Gi
zeabur volume mount --service "$API_ID" --volume api-data --path /app/data

zeabur service port expose --service "$API_ID" --port 8000

echo
echo "==> Triggering first deploy..."
zeabur deploy

echo
echo "✓ Done."
echo "  - API: https://<your-domain>.zeabur.app/docs"
echo "  - To update: zeabur deploy"
echo "  - To view logs: zeabur logs --service api"
