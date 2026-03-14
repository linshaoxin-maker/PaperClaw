"""Filtering service: relevance scoring and topic classification via LLM."""

from __future__ import annotations

from typing import Any

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from paper_agent.domain.models.paper import Paper
from paper_agent.infra.llm.llm_provider import LLMProvider
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage


class FilteringManager:
    def __init__(self, storage: SQLiteStorage, llm: LLMProvider) -> None:
        self._storage = storage
        self._llm = llm

    def filter_papers(
        self, papers: list[Paper], interests: dict[str, Any], show_progress: bool = True
    ) -> list[Paper]:
        if not papers:
            return []

        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
            ) as progress:
                task = progress.add_task("Filtering papers...", total=len(papers))
                for paper in papers:
                    self._score_paper(paper, interests)
                    progress.advance(task)
        else:
            for paper in papers:
                self._score_paper(paper, interests)

        return sorted(papers, key=lambda p: p.relevance_score, reverse=True)

    def _score_paper(self, paper: Paper, interests: dict[str, Any]) -> None:
        result = self._llm.score_relevance(paper, interests)
        paper.relevance_score = result["score"]
        paper.relevance_band = result["band"]
        paper.recommendation_reason = result["reason"]
        if result.get("topics"):
            paper.topics = result["topics"]
        paper.lifecycle_state = "filtered"

        self._storage.update_paper_scores(
            paper.id,
            score=paper.relevance_score,
            band=paper.relevance_band,
            reason=paper.recommendation_reason,
            topics=paper.topics if result.get("topics") else None,
        )
