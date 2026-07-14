"""SQLite + numpy vector store. No external service.
Ponytail: simple > scalable. 幾百份 doc 用 SQLite 完全 OK.
"""
import sqlite3
import numpy as np
from pathlib import Path
from .config import DB_PATH


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            vector BLOB NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON chunks(source)")
    return conn


def upsert_chunks(chunks, vectors):
    """chunks = [{id, text, source, chunk_index}, ...], vectors = [[float, ...], ...]"""
    conn = _connect()
    try:
        rows = [
            (c["id"], c["source"], c["chunk_index"], c["text"],
             np.asarray(v, dtype=np.float32).tobytes())
            for c, v in zip(chunks, vectors)
        ]
        conn.executemany(
            "INSERT OR REPLACE INTO chunks (id, source, chunk_index, text, vector) VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def search(query_vector, top_k=5):
    """Returns list of payloads ranked by cosine similarity."""
    conn = _connect()
    try:
        cur = conn.execute("SELECT id, source, chunk_index, text, vector FROM chunks")
        rows = cur.fetchall()
        if not rows:
            return []
        # Decode all vectors into a matrix
        ids, sources, indices, texts, blobs = zip(*rows)
        matrix = np.vstack([np.frombuffer(b, dtype=np.float32) for b in blobs])
        q = np.asarray(query_vector, dtype=np.float32)

        # Cosine similarity: (A · B) / (|A| * |B|)
        # Normalize
        matrix_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
        q_norm = q / (np.linalg.norm(q) + 1e-10)
        scores = matrix_norm @ q_norm

        # Top-k indices
        top_idx = np.argsort(-scores)[:top_k]
        return [
            {
                "id": ids[i],
                "source": sources[i],
                "chunk_index": indices[i],
                "text": texts[i],
                "_score": float(scores[i]),
            }
            for i in top_idx
        ]
    finally:
        conn.close()


def delete_by_source(source):
    conn = _connect()
    try:
        conn.execute("DELETE FROM chunks WHERE source = ?", (source,))
        conn.commit()
    finally:
        conn.close()


def list_sources():
    """Returns list of {source, chunks}."""
    conn = _connect()
    try:
        cur = conn.execute("""
            SELECT source, COUNT(*) as n
            FROM chunks
            GROUP BY source
            ORDER BY source
        """)
        return [{"source": s, "chunks": n} for s, n in cur.fetchall()]
    finally:
        conn.close()


def vector_size():
    """Returns the dimension of stored vectors. 0 if empty."""
    conn = _connect()
    try:
        cur = conn.execute("SELECT vector FROM chunks LIMIT 1")
        row = cur.fetchone()
        if row is None:
            return 0
        return len(np.frombuffer(row[0], dtype=np.float32))
    finally:
        conn.close()
