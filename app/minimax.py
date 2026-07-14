"""MiniMax API client (embeddings + chat). Single place to swap providers.

MiniMax /v1/embeddings spec (verified 2026-07-14):
  - request:  {"model": "embo-01", "texts": [...], "type": "db"|"query"}
  - response: {"vectors": [[float, ...], ...], "base_resp": {...}}
  - "db"    = embedding documents to store
  - "query" = embedding search queries
"""
import httpx
from .config import MINIMAX_API_KEY, MINIMAX_BASE_URL, EMBEDDING_MODEL, CHAT_MODEL


class MiniMax:
    def __init__(self):
        if not MINIMAX_API_KEY:
            raise RuntimeError(
                "MINIMAX_CN_API_KEY not set. Copy .env.example to .env and fill it in."
            )
        self._client = httpx.AsyncClient(
            base_url=MINIMAX_BASE_URL,
            headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
            timeout=60.0,
        )

    async def embed(self, texts, type_="db"):
        """Get embeddings. type_="db" for documents, "query" for search queries.
        Returns list of vectors.
        """
        resp = await self._client.post(
            "/embeddings",
            json={"model": EMBEDDING_MODEL, "texts": texts, "type": type_},
        )
        resp.raise_for_status()
        data = resp.json()

        # MiniMax response shape: {"vectors": [[...]], "base_resp": {...}}
        # Ponytail: trust the shape, but check status_code if present.
        base = data.get("base_resp", {})
        if base.get("status_code", 0) != 0:
            raise RuntimeError(f"MiniMax API error: {base.get('status_msg')}")

        vectors = data.get("vectors")
        if vectors is None:
            raise RuntimeError(f"MiniMax returned no vectors: {data}")
        return vectors

    async def embed_query(self, query):
        """Embed a single query string. Convenience wrapper."""
        vectors = await self.embed([query], type_="query")
        return vectors[0]

    async def chat(self, messages, stream=False):
        """Chat completion. messages = [{"role": "user", "content": "..."}, ...]"""
        resp = await self._client.post(
            "/chat/completions",
            json={
                "model": CHAT_MODEL,
                "messages": messages,
                "stream": stream,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def close(self):
        await self._client.aclose()


# Singleton
_client = None


def get_client():
    global _client
    if _client is None:
        _client = MiniMax()
    return _client
