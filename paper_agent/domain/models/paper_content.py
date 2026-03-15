"""Domain models for PDF full-text content."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class PaperSection:
    name: str
    heading: str
    text: str
    page_range: tuple[int, int] = (0, 0)


@dataclass
class PaperTable:
    caption: str
    headers: list[str]
    rows: list[list[str]]
    section: str = ""


@dataclass
class PaperContent:
    paper_id: str
    sections: list[PaperSection] = field(default_factory=list)
    tables: list[PaperTable] = field(default_factory=list)
    figure_captions: list[str] = field(default_factory=list)
    raw_text: str = ""
    parsed_at: datetime = field(default_factory=datetime.utcnow)

    def get_section(self, name: str) -> PaperSection | None:
        for s in self.sections:
            if s.name.lower() == name.lower():
                return s
        return None

    def get_sections_text(self, names: list[str] | None = None) -> str:
        if names is None:
            return "\n\n".join(s.text for s in self.sections)
        target = {n.lower() for n in names}
        return "\n\n".join(s.text for s in self.sections if s.name.lower() in target)

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "sections": [
                {
                    "name": s.name,
                    "heading": s.heading,
                    "text": s.text,
                    "page_range": list(s.page_range),
                }
                for s in self.sections
            ],
            "tables": [
                {
                    "caption": t.caption,
                    "headers": t.headers,
                    "rows": t.rows,
                    "section": t.section,
                }
                for t in self.tables
            ],
            "figure_captions": self.figure_captions,
            "parsed_at": self.parsed_at.isoformat() if self.parsed_at else None,
        }

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "section_count": len(self.sections),
            "table_count": len(self.tables),
            "figure_count": len(self.figure_captions),
            "sections": [
                {"name": s.name, "heading": s.heading, "page_range": list(s.page_range)}
                for s in self.sections
            ],
            "text_length": len(self.raw_text),
            "parsed_at": self.parsed_at.isoformat() if self.parsed_at else None,
        }
