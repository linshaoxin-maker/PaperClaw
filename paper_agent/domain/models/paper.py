from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Paper:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    canonical_key: str = ""
    source_name: str = ""
    source_paper_id: str = ""
    title: str = ""
    abstract: str = ""
    authors: list[str] = field(default_factory=list)
    published_at: datetime | None = None
    url: str = ""
    topics: list[str] = field(default_factory=list)
    methodology_tags: list[str] = field(default_factory=list)
    research_objectives: list[str] = field(default_factory=list)
    relevance_score: float = 0.0
    relevance_band: str = ""  # "high" | "low" | ""
    recommendation_reason: str = ""
    lifecycle_state: str = "discovered"
    metadata: dict[str, Any] = field(default_factory=dict)
    reading_status: str | None = None  # to_read | reading | read | important
    reading_status_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "source": self.source_name,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "url": self.url,
            "relevance_score": self.relevance_score,
            "topics": self.topics,
        }

    def to_compact_dict(self) -> dict[str, Any]:
        """Mid-level detail: enough for survey/compare, without raw noise."""
        abstract_short = self.abstract[:300] + "..." if len(self.abstract) > 300 else self.abstract
        authors_short = self.authors[:5] + (["et al."] if len(self.authors) > 5 else [])
        return {
            "id": self.id,
            "title": self.title,
            "authors": authors_short,
            "abstract": abstract_short,
            "source": self.source_name,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "url": self.url,
            "topics": self.topics,
            "score": self.relevance_score,
        }

    def to_detail_dict(self) -> dict[str, Any]:
        return {
            "object_type": "paper_detail",
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "source": self.source_name,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "url": self.url,
            "topics": self.topics,
            "methodology_tags": self.methodology_tags,
            "research_objectives": self.research_objectives,
            "relevance": {
                "score": self.relevance_score,
                "band": self.relevance_band,
            },
            "recommendation_reason": self.recommendation_reason,
            "lifecycle_state": self.lifecycle_state,
        }
