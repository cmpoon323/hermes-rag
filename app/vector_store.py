"""Qdrant wrapper. Single collection, cosine distance."""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from .config import QDRANT_HOST, QDRANT_PORT, QDRANT_PATH, COLLECTION_NAME


def get_client():
    """Connect to Qdrant. Use server mode if QDRANT_HOST is reachable, else embedded.
    Ponytail: keep both code paths, env var decides at runtime.
    """
    if QDRANT_HOST and QDRANT_HOST != "embedded":
        return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    # Embedded mode (Qdrant persists to QDRANT_PATH)
    return QdrantClient(path=QDRANT_PATH)


def ensure_collection(client, vector_size):
    """Create collection if not exists. Idempotent."""
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def upsert_chunks(client, chunks, vectors):
    """chunks = [{'id': str, 'text': str, 'source': str, 'chunk_index': int}, ...]"""
    points = [
        PointStruct(
            id=abs(hash(c["id"])) % (2**63),  # Qdrant needs int or UUID
            vector=v,
            payload=c,
        )
        for c, v in zip(chunks, vectors)
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)


def search(client, query_vector, top_k=5):
    """Returns list of payloads ranked by similarity."""
    hits = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
    )
    return [
        {**hit.payload, "_score": hit.score}
        for hit in hits
    ]


def delete_by_source(client, source):
    """Delete all chunks from a specific document."""
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector={"filter": {"must": [{"key": "source", "match": {"value": source}}]}},
    )


def list_sources(client):
    """List unique documents + chunk counts. Uses scroll with aggregation."""
    # Ponytail: simple scroll + group in Python. Don't add Qdrant aggregations
    # until we actually have > 10k docs.
    sources = {}
    offset = None
    while True:
        result = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        points, offset = result
        for p in points:
            src = p.payload.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1
        if offset is None:
            break
    return [{"source": s, "chunks": n} for s, n in sorted(sources.items())]
