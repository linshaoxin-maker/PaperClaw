from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from paper_agent.domain.models.paper import Paper


@dataclass
class QueryResult:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    query: str = ""
    mode: str = "retrieval"  # retrieval | qa | clustering | method | objective
    papers: list[Paper] = field(default_factory=list)
    answer: dict[str, Any] | None = None
    clusters: list[dict[str, Any]] | None = None
    status: str = "completed"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "object_type": "query_result",
            "id": self.id,
            "query": self.query,
            "mode": self.mode,
            "papers": [p.to_summary_dict() for p in self.papers],
        }
        if self.answer:
            result["answer"] = self.answer
        if self.clusters:
            result["clusters"] = self.clusters
        return result
