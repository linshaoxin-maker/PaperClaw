"""Digest generation: compile daily digest with high/low confidence zones."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from paper_agent.app.config_manager import ConfigProfile
from paper_agent.domain.models.digest import Digest, DigestStats
from paper_agent.domain.models.paper import Paper
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage


class DigestGenerator:
    def __init__(self, storage: SQLiteStorage, feedback_manager: Any = None) -> None:
        self._storage = storage
        self._feedback_manager = feedback_manager

    def generate_daily_digest(
        self, config: ConfigProfile, target_date: date | None = None
    ) -> Digest:
        target_date = target_date or date.today()
        since = target_date - timedelta(days=7)
        papers = self._storage.get_papers_by_date(since)

        if not papers:
            papers = self._storage.get_filtered_papers(min_score=0.0, limit=config.digest_top_n * 2)

        high = [p for p in papers if p.relevance_band == "high"]
        low = [p for p in papers if p.relevance_band == "low"]

        # Apply feedback-aware sorting: boost/demote based on topic preferences
        feedback_weights: dict[str, float] = {}
        if self._feedback_manager:
            try:
                feedback_weights = self._feedback_manager.get_adjusted_topic_weights()
            except Exception:
                pass

        def _feedback_adjusted_score(p: Paper) -> float:
            base = p.relevance_score
            if feedback_weights:
                for topic in p.topics:
                    if topic.lower() in feedback_weights:
                        base += feedback_weights[topic.lower()]
            return base

        high = sorted(high, key=_feedback_adjusted_score, reverse=True)[:config.digest_top_n]
        supplemental_count = max(0, config.digest_top_n - len(high))
        low = sorted(low, key=lambda p: p.relevance_score, reverse=True)[:supplemental_count]

        all_topics: list[str] = []
        for p in high + low:
            all_topics.extend(p.topics)
        top_topics = [t for t, _ in Counter(all_topics).most_common(5)]

        stats = DigestStats(
            total_collected=self._storage.count_papers(),
            total_filtered=len(papers),
            high_confidence_count=len(high),
            supplemental_count=len(low),
            top_topics=top_topics,
        )

        digest = Digest(
            digest_date=target_date,
            high_confidence_papers=high,
            supplemental_papers=low,
            stats=stats,
        )

        artifact_path = self._save_artifact(digest, config)
        digest.artifact_uri = str(artifact_path)
        self._storage.save_digest(digest)
        return digest

    def _save_artifact(self, digest: Digest, config: ConfigProfile) -> Path:
        artifacts_dir = Path(config.artifacts_dir) / "digests"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        path = artifacts_dir / f"digest-{digest.digest_date.isoformat()}.md"

        lines: list[str] = []
        lines.append(f"# Paper Agent Digest — {digest.digest_date.isoformat()}")
        lines.append("")
        lines.append(f"**Library size:** {digest.stats.total_collected} papers")
        lines.append(f"**High confidence:** {digest.stats.high_confidence_count} papers")
        lines.append(f"**Supplemental:** {digest.stats.supplemental_count} papers")
        if digest.stats.top_topics:
            lines.append(f"**Top topics:** {', '.join(digest.stats.top_topics)}")
        lines.append("")

        if digest.high_confidence_papers:
            lines.append("## High Confidence")
            lines.append("")
            for i, p in enumerate(digest.high_confidence_papers, 1):
                lines.extend(self._format_paper(i, p))

        if digest.supplemental_papers:
            lines.append("## Supplemental")
            lines.append("")
            for i, p in enumerate(digest.supplemental_papers, 1):
                lines.extend(self._format_paper(i, p))

        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def _format_paper(self, idx: int, paper: Paper) -> list[str]:
        meta_parts = [f"**Score:** {paper.relevance_score:.1f}/10"]
        if paper.venue or paper.source_name:
            meta_parts.append(f"**Venue:** {paper.venue or paper.source_name}")
        if paper.published_at:
            meta_parts.append(f"**Date:** {paper.published_at.strftime('%Y-%m-%d')}")
        if paper.canonical_key:
            meta_parts.append(f"**ID:** {paper.canonical_key}")
        if paper.citation_count:
            meta_parts.append(f"**Citations:** {paper.citation_count}")

        # Credibility signals from FilteringManager enrichment
        cred = (paper.metadata or {}).get("credibility_signals", {})
        venue_tier = cred.get("venue_tier")
        code_avail = cred.get("code_available")
        cred_parts: list[str] = []
        if venue_tier and venue_tier != "unknown":
            tier_labels = {"top": "🏆 Top Venue", "good": "✅ Good Venue", "preprint": "📄 Preprint", "workshop": "🔧 Workshop"}
            cred_parts.append(tier_labels.get(venue_tier, venue_tier))
        if code_avail:
            cred_parts.append("💻 Code")
        cit_vel = cred.get("citation_velocity")
        if cit_vel is not None and cit_vel > 0:
            cred_parts.append(f"📈 {cit_vel} cit/mo")

        # Authors: show up to 5, with "et al." if more
        authors_display = paper.authors[:5]
        if len(paper.authors) > 5:
            authors_display.append("et al.")

        lines = [
            f"### {idx}. {paper.title}",
            " | ".join(meta_parts),
            f"**Authors:** {', '.join(authors_display)}",
        ]
        if cred_parts:
            lines.append(f"**Credibility:** {' · '.join(cred_parts)}")
        if paper.topics:
            lines.append(f"**Topics:** {', '.join(paper.topics)}")
        if paper.methodology_tags:
            lines.append(f"**Methods:** {', '.join(paper.methodology_tags)}")
        # Links: show both abstract page and PDF
        links = []
        if paper.url:
            links.append(f"[Abstract]({paper.url})")
        if paper.pdf_url:
            links.append(f"[PDF]({paper.pdf_url})")
        if paper.doi:
            links.append(f"[DOI](https://doi.org/{paper.doi})")
        if links:
            lines.append(f"**Links:** {' · '.join(links)}")
        if paper.recommendation_reason:
            lines.append(f"**Why:** {paper.recommendation_reason}")
        if paper.abstract:
            abstract = paper.abstract[:500] + "..." if len(paper.abstract) > 500 else paper.abstract
            lines.append(f"> {abstract}")
        lines.append("")
        return lines
