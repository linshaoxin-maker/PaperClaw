"""Credibility assessment service for papers."""

from __future__ import annotations

from typing import Any

from paper_agent.domain.models.credibility import CredibilityAssessment
from paper_agent.domain.models.paper import Paper
from paper_agent.domain.models.paper_content import PaperContent
from paper_agent.infra.llm.llm_provider import LLMProvider
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage

_TOP_VENUES = {
    "neurips", "nips", "icml", "iclr", "cvpr", "iccv", "eccv", "aaai", "ijcai",
    "acl", "emnlp", "naacl", "sigir", "kdd",
    "icse", "fse", "osdi", "sosp", "sigmod", "vldb",
    "dac", "iccad", "date", "asp-dac", "ispd", "fpga", "www",
    "nature", "science", "cell", "pnas",
    "jmlr", "tpami", "tit", "tcad", "tse", "tosem",
    "tmlr",  # Transactions on Machine Learning Research
}

_GOOD_VENUES = {
    "coling", "eacl", "wacv", "bmvc", "cikm", "wsdm", "recsys",
    "icde",
    "ase", "issta", "msr", "saner", "issre",
    "ral", "iros", "icra",
    "isca", "micro", "hpca", "asplos",
    "glsvlsi", "islped",
    "aamas",
    # EDA-specific journals
    "todaes",  # ACM Trans. on Design Automation of Electronic Systems
    "tcas",    # IEEE Trans. on Circuits and Systems
    "integration",  # Integration, the VLSI Journal
    "tvlsi",   # IEEE Trans. on VLSI Systems
    "jetc",    # ACM Journal on Emerging Technologies in Computing
}


def _classify_venue(venue: str) -> str:
    if not venue:
        return "unknown"
    v_lower = venue.lower().strip()
    if "arxiv" in v_lower or "preprint" in v_lower:
        return "preprint"
    # Workshop detection must come before top-venue check
    # (e.g. "ICLR 2024 Workshop" should be workshop, not top)
    if "workshop" in v_lower:
        return "workshop"
    # Use word-boundary-aware matching to avoid false positives
    # e.g. "date" should match "DATE" conference, not "updated"
    import re
    for top in _TOP_VENUES:
        # Match as whole word (case-insensitive)
        if re.search(rf'\b{re.escape(top)}\b', v_lower):
            return "top"
    for good in _GOOD_VENUES:
        if re.search(rf'\b{re.escape(good)}\b', v_lower):
            return "good"
    # Check for journal indicators
    if any(kw in v_lower for kw in ("journal", "transactions", "letters")):
        return "good"
    return "unknown"


class CredibilityAssessor:
    def __init__(self, storage: SQLiteStorage, llm: LLMProvider) -> None:
        self._storage = storage
        self._llm = llm

    def quick_signals(self, paper: Paper) -> dict[str, Any]:
        """Lightweight credibility signals from metadata only (no LLM call).

        Returns venue_tier, code_available, citation_velocity for use in
        filtering/digest without the cost of a full LLM assessment.
        """
        venue_str = paper.venue or paper.metadata.get("venue", "") or paper.source_name
        venue_tier = _classify_venue(venue_str)
        code_url = paper.metadata.get("code_url") or paper.metadata.get("github_url")
        code_available = bool(code_url)
        citation_count = paper.citation_count or paper.metadata.get("citation_count") or paper.metadata.get("citationCount")
        citation_velocity = None
        if citation_count and paper.published_at:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            pub = paper.published_at
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            months = max((now - pub).days / 30.0, 1.0)
            citation_velocity = round(int(citation_count) / months, 2)
        return {
            "venue_tier": venue_tier,
            "code_available": code_available,
            "citation_count": citation_count,
            "citation_velocity": citation_velocity,
        }

    def assess(
        self,
        paper: Paper,
        content: PaperContent | None = None,
    ) -> CredibilityAssessment:
        """Full credibility assessment for a paper."""
        existing = self._storage.get_credibility_assessment(paper.id)
        if existing:
            return existing

        # Venue classification
        venue_str = paper.venue or paper.metadata.get("venue", "") or paper.source_name
        venue_tier = _classify_venue(venue_str)

        # Code / citation from metadata or S2
        code_url = paper.metadata.get("code_url") or paper.metadata.get("github_url")
        code_available = bool(code_url)
        citation_count = paper.metadata.get("citation_count")

        # Citation velocity
        citation_velocity = None
        if citation_count and paper.published_at:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            pub = paper.published_at
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            months = max((now - pub).days / 30.0, 1.0)
            citation_velocity = round(citation_count / months, 2)

        # LLM-based assessment of claims and baselines
        text_for_analysis = f"Title: {paper.title}\nAbstract: {paper.abstract}"
        if content and content.raw_text:
            experiments = content.get_section("experiments")
            conclusion = content.get_section("conclusion")
            extra = ""
            if experiments:
                extra += f"\n\nExperiments:\n{experiments.text[:3000]}"
            if conclusion:
                extra += f"\n\nConclusion:\n{conclusion.text[:1000]}"
            text_for_analysis += extra

        llm_assessment = self._llm.assess_credibility(text_for_analysis)

        assessment = CredibilityAssessment(
            paper_id=paper.id,
            code_available=code_available,
            code_url=code_url,
            open_data=llm_assessment.get("open_data"),
            venue_tier=venue_tier,
            citation_count=citation_count,
            citation_velocity=citation_velocity,
            claim_aggressiveness=llm_assessment.get("claim_aggressiveness", "unknown"),
            baseline_completeness=llm_assessment.get("baseline_completeness", "unknown"),
            reproducibility_risk=llm_assessment.get("reproducibility_risk", "unknown"),
            overall_confidence=llm_assessment.get("overall_confidence", "unknown"),
            assessment_notes=llm_assessment.get("notes", ""),
        )

        self._storage.save_credibility_assessment(assessment)
        return assessment

    def assess_batch(
        self,
        papers: list[Paper],
        contents: dict[str, PaperContent] | None = None,
    ) -> list[CredibilityAssessment]:
        """Batch credibility assessment."""
        contents = contents or {}
        return [self.assess(p, contents.get(p.id)) for p in papers]

    def enrich_from_s2(self, paper: Paper) -> dict[str, Any]:
        """Fetch additional credibility signals from Semantic Scholar."""
        import httpx

        s2_id = paper.metadata.get("s2_id") or paper.source_paper_id
        if not s2_id:
            return {}

        try:
            url = f"https://api.semanticscholar.org/graph/v1/paper/{s2_id}"
            client = httpx.Client(timeout=15.0, follow_redirects=True, trust_env=True)
            resp = client.get(
                url,
                params={"fields": "citationCount,influentialCitationCount,openAccessPdf,isOpenAccess,venue"},
            )
            client.close()

            if resp.status_code != 200:
                return {}

            data = resp.json()
            enrichment: dict[str, Any] = {}
            if data.get("citationCount") is not None:
                enrichment["citation_count"] = data["citationCount"]
            if data.get("influentialCitationCount") is not None:
                enrichment["influential_citations"] = data["influentialCitationCount"]
            if data.get("isOpenAccess") is not None:
                enrichment["open_access"] = data["isOpenAccess"]
            if data.get("venue"):
                enrichment["venue"] = data["venue"]
            return enrichment
        except Exception:
            return {}
