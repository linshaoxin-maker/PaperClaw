"""Filtering service: relevance scoring and topic classification via LLM."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from paper_agent.domain.models.paper import Paper
from paper_agent.infra.llm.llm_provider import LLMProvider
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage

logger = logging.getLogger(__name__)

_MAX_WORKERS = 8


class FilteringManager:
    def __init__(self, storage: SQLiteStorage, llm: LLMProvider) -> None:
        self._storage = storage
        self._llm = llm

    def filter_papers(
        self, papers: list[Paper], interests: dict[str, Any], show_progress: bool = True
    ) -> list[Paper]:
        if not papers:
            return []

        results: list[tuple[Paper, dict[str, Any]]] = []
        failed = 0

        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
            ) as progress:
                task = progress.add_task("Filtering papers...", total=len(papers))
                with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
                    futures = {
                        pool.submit(self._call_llm, paper, interests): paper
                        for paper in papers
                    }
                    for future in as_completed(futures):
                        paper = futures[future]
                        result = future.result()
                        results.append((paper, result))
                        if result.get("reason") == "LLM 评分失败":
                            failed += 1
                        progress.advance(task)
        else:
            with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
                futures = {
                    pool.submit(self._call_llm, paper, interests): paper
                    for paper in papers
                }
                for future in as_completed(futures):
                    paper = futures[future]
                    result = future.result()
                    results.append((paper, result))
                    if result.get("reason") == "LLM 评分失败":
                        failed += 1

        for paper, result in results:
            self._apply_and_persist(paper, result)

        if failed:
            logger.warning("LLM scoring failed for %d/%d papers", failed, len(papers))

        return sorted(papers, key=lambda p: p.relevance_score, reverse=True)

    def _call_llm(self, paper: Paper, interests: dict[str, Any]) -> dict[str, Any]:
        """Call LLM for relevance scoring (thread-safe, no DB access)."""
        try:
            return self._llm.score_relevance(paper, interests)
        except Exception:
            logger.warning("LLM call failed for paper %s, assigning score 0", paper.id)
            return {"score": 0.0, "band": "low", "reason": "LLM 评分失败", "topics": []}

    def _apply_and_persist(self, paper: Paper, result: dict[str, Any]) -> None:
        """Apply LLM result to paper object and persist to DB (main thread only)."""
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
