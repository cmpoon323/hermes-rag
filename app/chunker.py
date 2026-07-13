"""Text chunker. Recursive character splitter, sentence-aware.
Ponytail: don't pull in langchain. Stdlib + 30 lines.
"""
import re
from .config import CHUNK_SIZE, CHUNK_OVERLAP


def _split_sentences(text: str) -> list[str]:
    """Rough sentence split. Good enough for English/Chinese mixed text."""
    # Split on 。！？. ! ? followed by whitespace or newline
    parts = re.split(r'(?<=[。！？.!?\n])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text: str, source: str) -> list[dict]:
    """Split text into ~CHUNK_SIZE char chunks with CHUNK_OVERLAP overlap.
    Returns list of {id, text, source, chunk_index}.
    """
    sentences = _split_sentences(text)
    chunks = []
    current = []
    current_len = 0
    idx = 0

    for sent in sentences:
        sent_len = len(sent)
        # If adding this sentence exceeds CHUNK_SIZE and we have content, flush
        if current and current_len + sent_len > CHUNK_SIZE:
            chunk_text_str = " ".join(current)
            chunks.append({
                "id": f"{source}::{idx}",
                "text": chunk_text_str,
                "source": source,
                "chunk_index": idx,
            })
            idx += 1
            # Keep last ~CHUNK_OVERLAP chars worth of sentences for overlap
            overlap_buf = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s) > CHUNK_OVERLAP:
                    break
                overlap_buf.insert(0, s)
                overlap_len += len(s)
            current = overlap_buf
            current_len = overlap_len

        current.append(sent)
        current_len += sent_len

    # Flush remainder
    if current:
        chunks.append({
            "id": f"{source}::{idx}",
            "text": " ".join(current),
            "source": source,
            "chunk_index": idx,
        })

    return chunks
