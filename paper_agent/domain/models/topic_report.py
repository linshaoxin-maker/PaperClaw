from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from paper_agent.domain.models.paper import Paper


@dataclass
class TopicReport:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    topic: str = ""
    sections: list[dict[str, Any]] = field(default_factory=list)
    papers: list[Paper] = field(default_factory=list)
    artifact_uri: str | None = None
    status: str = "generated"
    version_tag: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_type": "topic_report",
            "id": self.id,
            "topic": self.topic,
            "sections": self.sections,
            "papers": [p.to_summary_dict() for p in self.papers],
            "artifact_uri": self.artifact_uri,
            "report_version": self.version_tag,
        }
