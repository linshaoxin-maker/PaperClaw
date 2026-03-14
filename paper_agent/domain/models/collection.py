from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CollectionRecord:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    source_name: str = ""
    trigger_type: str = "manual"  # manual | scheduled | initialization
    status: str = "running"  # running | completed | failed
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    collected_count: int = 0
    new_count: int = 0
    duplicate_count: int = 0
    error_summary: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_name": self.source_name,
            "trigger_type": self.trigger_type,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "collected_count": self.collected_count,
            "new_count": self.new_count,
            "duplicate_count": self.duplicate_count,
        }
