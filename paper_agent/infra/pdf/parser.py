"""PDF text extraction using PyMuPDF."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def extract_pages(pdf_path: str | Path) -> list[dict[str, Any]]:
    """Extract text and metadata from each page of a PDF.

    Returns a list of dicts: {"page": int, "text": str, "width": float, "height": float}.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(str(pdf_path))
    pages: list[dict[str, Any]] = []
    try:
        for i, page in enumerate(doc):
            pages.append({
                "page": i,
                "text": page.get_text("text"),
                "width": page.rect.width,
                "height": page.rect.height,
            })
    finally:
        doc.close()
    return pages


def extract_full_text(pdf_path: str | Path) -> str:
    """Extract the full text of a PDF, concatenated across pages."""
    pages = extract_pages(pdf_path)
    return "\n\n".join(p["text"] for p in pages)


def extract_figure_captions(pages: list[dict[str, Any]]) -> list[str]:
    """Heuristic extraction of figure captions from page texts."""
    import re

    captions: list[str] = []
    pattern = re.compile(
        r"((?:Figure|Fig\.?)\s*\d+[.:]\s*.+?)(?:\n\n|\n(?=[A-Z0-9])|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    for page in pages:
        for m in pattern.finditer(page["text"]):
            caption = m.group(1).strip()
            if len(caption) > 10:
                captions.append(caption)
    return captions
