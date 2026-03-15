"""Domain model for paper credibility assessment."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CredibilityAssessment:
    paper_id: str
    code_available: bool | None = None
    code_url: str | None = None
    open_data: bool | None = None
    venue_tier: str = "unknown"  # "top" | "good" | "workshop" | "preprint" | "unknown"
    citation_count: int | None = None
    citation_velocity: float | None = None  # citations per month
    claim_aggressiveness: str = "unknown"  # "conservative" | "moderate" | "aggressive"
    baseline_completeness: str = "unknown"  # "comprehensive" | "adequate" | "insufficient"
    reproducibility_risk: str = "unknown"  # "low" | "medium" | "high"
    overall_confidence: str = "unknown"  # "high" | "medium" | "low"
    assessment_notes: str = ""
    assessed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "code_available": self.code_available,
            "code_url": self.code_url,
            "open_data": self.open_data,
            "venue_tier": self.venue_tier,
            "citation_count": self.citation_count,
            "citation_velocity": self.citation_velocity,
            "claim_aggressiveness": self.claim_aggressiveness,
            "baseline_completeness": self.baseline_completeness,
            "reproducibility_risk": self.reproducibility_risk,
            "overall_confidence": self.overall_confidence,
            "assessment_notes": self.assessment_notes,
            "assessed_at": self.assessed_at.isoformat() if self.assessed_at else None,
        }

    @property
    def read_priority(self) -> str:
        """Suggest read priority based on credibility signals."""
        if self.overall_confidence == "high":
            return "精读"
        elif self.overall_confidence == "medium":
            return "略读"
        return "跳过"
