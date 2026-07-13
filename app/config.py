"""Centralized config. Read once, fail fast."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# === MiniMax ===
# Ponytail: don't fail at import. Fail when client is first used.
# (chunker/parsers need to work without a key for tests)
MINIMAX_API_KEY = os.getenv("MINIMAX_CN_API_KEY", "")
MINIMAX_BASE_URL = os.getenv("MINIMAX_CN_BASE_URL", "https://api.minimaxi.com/v1")

# === Qdrant ===
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_PATH = os.getenv("QDRANT_PATH", "./data/qdrant")

# === RAG params ===
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "docs")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "embo-01")
CHAT_MODEL = os.getenv("CHAT_MODEL", "MiniMax-Text-01")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
TOP_K = int(os.getenv("TOP_K", "5"))

# === Paths ===
DATA_DIR = Path("./data")
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
