"""FastAPI app: upload + chat + admin endpoints."""
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import UPLOAD_DIR
from .ingest import ingest_file
from .qa import answer
from . import vector_store

app = FastAPI(title="Hermes RAG", version="0.1.0")

# CORS: Streamlit UI runs on different port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ponytail: single-user, no auth → no CORS lockdown needed
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """Upload a PDF or DOCX, ingest it."""
    if not file.filename:
        raise HTTPException(400, "No filename")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".pdf", ".docx", ".doc"):
        raise HTTPException(400, f"Unsupported file type: {ext}")

    # Save to disk
    dest = UPLOAD_DIR / file.filename
    content = await file.read()
    dest.write_bytes(content)

    # Ingest
    result = await ingest_file(dest)
    return result


class AskRequest(BaseModel):
    question: str
    top_k: int | None = None


@app.post("/ask")
async def ask(req: AskRequest):
    """Ask a question. Returns answer + source chunks."""
    return await answer(req.question, top_k=req.top_k or 5)


@app.get("/documents")
async def documents():
    """List all ingested documents + chunk counts."""
    qdrant = vector_store.get_client()
    return {"documents": vector_store.list_sources(qdrant)}


@app.delete("/documents/{source:path}")
async def delete_document(source: str):
    """Delete all chunks from a document."""
    qdrant = vector_store.get_client()
    vector_store.delete_by_source(qdrant, source)
    return {"deleted": source}
