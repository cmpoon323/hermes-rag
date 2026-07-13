"""Ingestion pipeline: file → parse → chunk → embed → Qdrant."""
from pathlib import Path
from .parsers import parse
from .chunker import chunk_text
from .minimax import get_client as get_minimax
from . import vector_store


async def ingest_file(path: Path) -> dict:
    """Process one file end-to-end. Returns summary."""
    text = parse(path)
    if not text.strip():
        return {"source": path.name, "chunks": 0, "error": "empty document"}

    chunks = chunk_text(text, source=path.name)
    if not chunks:
        return {"source": path.name, "chunks": 0, "error": "no chunks produced"}

    # Embed in batch (MiniMax supports batch)
    minimax = get_minimax()
    vectors = await minimax.embed([c["text"] for c in chunks])

    # Store
    qdrant = vector_store.get_client()
    vector_store.ensure_collection(qdrant, vector_size=len(vectors[0]))
    vector_store.upsert_chunks(qdrant, chunks, vectors)

    return {
        "source": path.name,
        "chunks": len(chunks),
        "vector_size": len(vectors[0]),
        "chars": len(text),
    }
