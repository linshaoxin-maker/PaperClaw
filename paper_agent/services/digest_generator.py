"""Digest generation: compile daily digest with high/low confidence zones."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

from paper_agent.app.config_manager import ConfigProfile
from paper_agent.domain.models.digest import Digest, DigestStats
from paper_agent.domain.models.paper import Paper
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage


class DigestGenerator:
    def __init__(self, storage: SQLiteStorage) -> None:
        self._storage = storage

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

        high = sorted(high, key=lambda p: p.relevance_score, reverse=True)[:config.digest_top_n]
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
        if paper.source_name:
            meta_parts.append(f"**Source:** {paper.source_name}")
        if paper.published_at:
            meta_parts.append(f"**Date:** {paper.published_at.strftime('%Y-%m-%d')}")
        if paper.canonical_key:
            meta_parts.append(f"**ID:** {paper.canonical_key}")

        lines = [
            f"### {idx}. {paper.title}",
            " | ".join(meta_parts),
            f"**Authors:** {', '.join(paper.authors[:3])}",
        ]
        if paper.topics:
            lines.append(f"**Topics:** {', '.join(paper.topics)}")
        if paper.methodology_tags:
            lines.append(f"**Methods:** {', '.join(paper.methodology_tags)}")
        lines.append(f"**Link:** {paper.url}")
        if paper.recommendation_reason:
            lines.append(f"**Why:** {paper.recommendation_reason}")
        if paper.abstract:
            abstract = paper.abstract[:300] + "..." if len(paper.abstract) > 300 else paper.abstract
            lines.append(f"> {abstract}")
        lines.append("")
        return lines
