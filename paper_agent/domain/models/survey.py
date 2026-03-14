from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from paper_agent.domain.models.paper import Paper


@dataclass
class Survey:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    entry_point: str = ""
    entry_point_type: str = "topic"  # topic | method | objective | combined
    problem_definition: str = ""
    method_taxonomy: list[dict[str, Any]] = field(default_factory=list)
    comparative_analysis: dict[str, Any] | None = None
    research_gaps: list[str] = field(default_factory=list)
    future_directions: list[str] = field(default_factory=list)
    sections: list[dict[str, Any]] = field(default_factory=list)
    papers: list[Paper] = field(default_factory=list)
    artifact_uri: str | None = None
    status: str = "generated"
    version_tag: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_type": "survey",
            "id": self.id,
            "entry_point": self.entry_point,
            "entry_point_type": self.entry_point_type,
            "problem_definition": self.problem_definition,
            "method_taxonomy": self.method_taxonomy,
            "comparative_analysis": self.comparative_analysis,
            "research_gaps": self.research_gaps,
            "future_directions": self.future_directions,
            "sections": self.sections,
            "papers": [p.to_summary_dict() for p in self.papers],
            "artifact_uri": self.artifact_uri,
            "survey_version": self.version_tag,
        }
