"""Structured information extraction service."""

from __future__ import annotations

from typing import Any

from paper_agent.domain.models.paper import Paper
from paper_agent.domain.models.paper_content import PaperContent
from paper_agent.domain.models.paper_profile import PaperProfile
from paper_agent.infra.llm.llm_provider import LLMProvider
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage


class ExtractionEngine:
    def __init__(self, storage: SQLiteStorage, llm: LLMProvider) -> None:
        self._storage = storage
        self._llm = llm

    def extract_profile(
        self,
        paper: Paper,
        content: PaperContent | None = None,
        force: bool = False,
    ) -> PaperProfile:
        """Extract a structured profile from a paper.

        Uses full text if PaperContent is available, otherwise degrades
        to abstract-only extraction.
        """
        if not force:
            existing = self._storage.get_paper_profile(paper.id)
            if existing:
                return existing

        if content and content.raw_text:
            text_for_extraction = self._prepare_fulltext(content)
            extracted_from = "fulltext"
        else:
            text_for_extraction = f"Title: {paper.title}\nAbstract: {paper.abstract}"
            extracted_from = "abstract"

        raw = self._llm.extract_structured(text_for_extraction, _PROFILE_SCHEMA)

        profile = PaperProfile(
            paper_id=paper.id,
            task=raw.get("task", ""),
            method_family=raw.get("method_family", ""),
            method_name=raw.get("method_name", ""),
            datasets=raw.get("datasets", []),
            baselines=raw.get("baselines", []),
            metrics=raw.get("metrics", []),
            best_results=raw.get("best_results", {}),
            code_url=raw.get("code_url"),
            venue=raw.get("venue", ""),
            compute_cost=raw.get("compute_cost"),
            limitations=raw.get("limitations", []),
            extracted_from=extracted_from,
        )

        self._storage.save_paper_profile(profile)
        return profile

    def extract_profiles_batch(
        self,
        papers: list[Paper],
        contents: dict[str, PaperContent] | None = None,
    ) -> list[PaperProfile]:
        """Extract profiles for multiple papers."""
        contents = contents or {}
        profiles: list[PaperProfile] = []
        for paper in papers:
            content = contents.get(paper.id)
            profile = self.extract_profile(paper, content)
            profiles.append(profile)
        return profiles

    def build_comparison_table(self, paper_ids: list[str]) -> dict[str, Any]:
        """Build a structured comparison table from paper profiles."""
        profiles: list[PaperProfile] = []
        missing: list[str] = []

        for pid in paper_ids:
            profile = self._storage.get_paper_profile(pid)
            if profile:
                profiles.append(profile)
            else:
                missing.append(pid)

        if not profiles:
            return {"error": "No profiles found. Run paper_extract first.", "missing": missing}

        headers = ["paper_id", "task", "method", "datasets", "baselines", "metrics",
                    "best_results", "code", "venue", "compute_cost"]
        rows = [p.to_comparison_row() for p in profiles]

        return {
            "headers": headers,
            "rows": rows,
            "count": len(profiles),
            "missing": missing,
        }

    def query_profiles(self, filters: dict[str, str]) -> list[PaperProfile]:
        """Query across stored profiles using field filters."""
        return self._storage.query_paper_profiles(filters)

    def field_stats(self, field: str) -> dict[str, int]:
        """Aggregate stats for a profile field (e.g. method_family distribution)."""
        return self._storage.get_profile_field_stats(field)

    def _prepare_fulltext(self, content: PaperContent) -> str:
        """Prepare text for LLM extraction, prioritizing key sections."""
        priority_sections = ["abstract", "method", "experiments", "results", "conclusion"]
        parts: list[str] = []

        for name in priority_sections:
            section = content.get_section(name)
            if section:
                parts.append(f"## {section.heading}\n{section.text}")

        for section in content.sections:
            if section.name not in priority_sections:
                parts.append(f"## {section.heading}\n{section.text[:1000]}")

        text = "\n\n".join(parts)
        # Truncate to avoid exceeding LLM context
        if len(text) > 30000:
            text = text[:30000] + "\n\n[truncated]"
        return text


_PROFILE_SCHEMA = {
    "task": "The main task or problem being addressed (e.g. 'VLSI placement', 'image classification')",
    "method_family": "The broad method family (e.g. 'reinforcement learning', 'graph neural network', 'transformer')",
    "method_name": "The specific method or algorithm name (e.g. 'DREAMPlace', 'ResNet-50')",
    "datasets": "List of datasets or benchmarks used (e.g. ['ISPD2005', 'ICCAD2015'])",
    "baselines": "List of baseline methods compared against (e.g. ['ePlace', 'RePlAce'])",
    "metrics": "List of evaluation metrics (e.g. ['HPWL', 'runtime', 'accuracy'])",
    "best_results": "Dict of metric -> best result (e.g. {'HPWL': '3.2% improvement', 'runtime': '2x faster'})",
    "code_url": "URL to code repository if mentioned, else null",
    "venue": "Publication venue (e.g. 'DAC 2024', 'NeurIPS 2023', 'arXiv preprint')",
    "compute_cost": "Computational cost if mentioned (e.g. '8x A100, 24h'), else null",
    "limitations": "List of limitations mentioned by the authors",
}
