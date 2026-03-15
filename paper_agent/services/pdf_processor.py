"""PDF processing service: parse, store, and retrieve paper content."""

from __future__ import annotations

import re
from pathlib import Path

from paper_agent.domain.models.paper_content import PaperContent
from paper_agent.infra.pdf.parser import extract_figure_captions, extract_pages
from paper_agent.infra.pdf.section_splitter import split_sections
from paper_agent.infra.pdf.table_extractor import assign_tables_to_sections, extract_tables
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage


class PdfProcessor:
    def __init__(self, storage: SQLiteStorage) -> None:
        self._storage = storage

    def parse_pdf(self, pdf_path: str | Path) -> PaperContent:
        """Parse a PDF into structured PaperContent (without storing)."""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        pages = extract_pages(pdf_path)
        full_text = "\n\n".join(p["text"] for p in pages)

        sections = split_sections(full_text, page_texts=pages)
        tables = extract_tables(pdf_path)
        figure_captions = extract_figure_captions(pages)

        assign_tables_to_sections(tables, sections)

        return PaperContent(
            paper_id="",
            sections=sections,
            tables=tables,
            figure_captions=figure_captions,
            raw_text=full_text,
        )

    def parse_and_store(self, paper_id: str, pdf_path: str | Path) -> PaperContent:
        """Parse a PDF and store the result linked to a paper."""
        content = self.parse_pdf(pdf_path)
        content.paper_id = paper_id
        self._storage.save_paper_content(content)
        return content

    def get_content(self, paper_id: str) -> PaperContent | None:
        """Retrieve previously parsed content for a paper."""
        return self._storage.get_paper_content(paper_id)

    def find_pdf_for_paper(self, paper_id: str, search_dirs: list[str | Path] | None = None) -> Path | None:
        """Try to find a downloaded PDF for a paper in common locations."""
        paper = self._storage.get_paper(paper_id)
        if not paper:
            return None

        arxiv_id = paper.source_paper_id
        if not arxiv_id and paper.canonical_key.startswith("arxiv:"):
            arxiv_id = paper.canonical_key[6:]

        dirs_to_search = [Path("papers"), Path.cwd() / "papers"]
        if search_dirs:
            dirs_to_search = [Path(d) for d in search_dirs] + dirs_to_search

        for d in dirs_to_search:
            if not d.exists():
                continue
            for f in d.glob("*.pdf"):
                if arxiv_id and arxiv_id in f.name:
                    return f
                title_slug = re.sub(r"[^\w\s-]", "", paper.title or "")[:80].strip().replace(" ", "_")
                if title_slug and title_slug in f.name:
                    return f

        return None
