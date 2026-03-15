"""Domain model for structured paper profile (extracted metadata)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class PaperProfile:
    paper_id: str
    task: str = ""
    method_family: str = ""
    method_name: str = ""
    datasets: list[str] = field(default_factory=list)
    baselines: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    best_results: dict[str, str] = field(default_factory=dict)
    code_url: str | None = None
    venue: str = ""
    compute_cost: str | None = None
    limitations: list[str] = field(default_factory=list)
    extracted_from: str = "abstract"  # "abstract" | "fulltext"
    extracted_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "task": self.task,
            "method_family": self.method_family,
            "method_name": self.method_name,
            "datasets": self.datasets,
            "baselines": self.baselines,
            "metrics": self.metrics,
            "best_results": self.best_results,
            "code_url": self.code_url,
            "venue": self.venue,
            "compute_cost": self.compute_cost,
            "limitations": self.limitations,
            "extracted_from": self.extracted_from,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
        }

    def to_comparison_row(self) -> dict[str, Any]:
        """Flat dict suitable for tabular comparison."""
        return {
            "paper_id": self.paper_id,
            "task": self.task,
            "method": self.method_name or self.method_family,
            "datasets": ", ".join(self.datasets) if self.datasets else "",
            "baselines": ", ".join(self.baselines) if self.baselines else "",
            "metrics": ", ".join(self.metrics) if self.metrics else "",
            "best_results": "; ".join(f"{k}: {v}" for k, v in self.best_results.items()) if self.best_results else "",
            "code": self.code_url or "",
            "venue": self.venue,
            "compute_cost": self.compute_cost or "",
        }
