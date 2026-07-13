"""Document parsers: PDF + Word → plain text.
Ponytail: no abstract BaseParser class. One function per file type, dispatch in ingest().
"""
from pathlib import Path
import fitz  # PyMuPDF
import docx


def parse_pdf(path: Path) -> str:
    """Extract text from PDF. Uses PyMuPDF (fast, handles most PDFs)."""
    doc = fitz.open(path)
    parts = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    return "\n\n".join(parts)


def parse_docx(path: Path) -> str:
    """Extract text from .docx. Paragraphs only (no tables/images)."""
    d = docx.Document(path)
    return "\n\n".join(p.text for p in d.paragraphs if p.text.strip())


def parse(path: Path) -> str:
    """Dispatch by extension."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        return parse_pdf(path)
    if ext in (".docx", ".doc"):
        return parse_docx(path)
    raise ValueError(f"Unsupported file type: {ext}")


# Future hook for OCR fallback (Phase P2 polish)
def parse_with_ocr_fallback(path: Path) -> str:
    """Try regular parse; if text is too short, suspect scanned PDF → OCR.
    Ponytail: keep this stub until you actually hit a scanned PDF.
    """
    text = parse(path)
    if len(text.strip()) < 100 and path.suffix.lower() == ".pdf":
        # TODO: call Mistral OCR
        # from .ocr import mistral_ocr
        # return mistral_ocr(path)
        raise NotImplementedError("OCR fallback not yet wired. Add Mistral OCR here.")
    return text
