"""MiniMax API client (embeddings + chat). Single place to swap providers."""
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

    async def embed(self, texts):
        """Get embeddings for a list of texts. Returns list of vectors."""
        # MiniMax API expects {"texts": [...]} not {"input": [...]}
        resp = await self._client.post(
            "/embeddings",
            json={"model": EMBEDDING_MODEL, "texts": texts},
        )
        resp.raise_for_status()
        data = resp.json()
        # Ponytail: trust the shape MiniMax returns, don't over-normalize
        return [item["embedding"] for item in data["data"]]

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
