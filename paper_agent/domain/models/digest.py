from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from paper_agent.domain.models.paper import Paper


@dataclass
class DigestStats:
    total_collected: int = 0
    total_filtered: int = 0
    high_confidence_count: int = 0
    supplemental_count: int = 0
    top_topics: list[str] = field(default_factory=list)


@dataclass
class Digest:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    digest_date: date = field(default_factory=date.today)
    status: str = "generated"
    high_confidence_papers: list[Paper] = field(default_factory=list)
    supplemental_papers: list[Paper] = field(default_factory=list)
    stats: DigestStats = field(default_factory=DigestStats)
    artifact_uri: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_type": "digest",
            "id": self.id,
            "date": self.digest_date.isoformat(),
            "summary": {
                "total_collected": self.stats.total_collected,
                "total_filtered": self.stats.total_filtered,
                "high_confidence_count": self.stats.high_confidence_count,
                "supplemental_count": self.stats.supplemental_count,
                "top_topics": self.stats.top_topics,
            },
            "high_confidence_papers": [p.to_summary_dict() for p in self.high_confidence_papers],
            "supplemental_papers": [p.to_summary_dict() for p in self.supplemental_papers],
            "artifact_uri": self.artifact_uri,
        }
