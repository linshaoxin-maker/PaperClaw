"""Extract tables from PDF using PyMuPDF's built-in table detection."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from paper_agent.domain.models.paper_content import PaperTable


def extract_tables(pdf_path: str | Path) -> list[PaperTable]:
    """Extract tables from a PDF file.

    Uses PyMuPDF's find_tables() API (available since pymupdf 1.23).
    Falls back gracefully if the API is unavailable.
    """
    import fitz

    doc = fitz.open(str(pdf_path))
    tables: list[PaperTable] = []

    try:
        for page_num, page in enumerate(doc):
            try:
                tab_finder = page.find_tables()
            except AttributeError:
                continue

            page_text = page.get_text("text")

            for tab in tab_finder.tables:
                data = tab.extract()
                if not data or len(data) < 2:
                    continue

                headers = [str(cell or "").strip() for cell in data[0]]
                rows = [
                    [str(cell or "").strip() for cell in row]
                    for row in data[1:]
                ]

                caption = _find_nearest_caption(page_text, tab.bbox, page_num)

                tables.append(PaperTable(
                    caption=caption,
                    headers=headers,
                    rows=rows,
                    section="",
                ))
    finally:
        doc.close()

    return tables


def _find_nearest_caption(
    page_text: str,
    bbox: tuple[float, ...],
    page_num: int,
) -> str:
    """Heuristic: find 'Table N:' or 'Table N.' caption near the table bbox."""
    pattern = re.compile(
        r"(Table\s+\d+[.:]\s*.+?)(?:\n\n|\n(?=[A-Z0-9])|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    for m in pattern.finditer(page_text):
        caption = m.group(1).strip()
        if len(caption) > 5:
            return caption
    return f"Table on page {page_num + 1}"


def assign_tables_to_sections(
    tables: list[PaperTable],
    sections: list[Any],
) -> None:
    """Best-effort assignment of tables to sections by checking if table
    caption text appears within a section's text."""
    for table in tables:
        if table.section:
            continue
        cap_lower = table.caption.lower()
        for section in sections:
            if cap_lower in section.text.lower() or any(
                h.lower() in section.text.lower() for h in table.headers if h
            ):
                table.section = section.name
                break
