"""Filtering service: relevance scoring and topic classification via LLM.

v04-experience: batch scoring, title pre-filter, feedback integration.
"""

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
_DEFAULT_BATCH_SIZE = 5


class FilteringManager:
    def __init__(
        self,
        storage: SQLiteStorage,
        llm: LLMProvider,
        feedback_manager: Any | None = None,
        batch_size: int = _DEFAULT_BATCH_SIZE,
        pre_filter_enabled: bool = True,
    ) -> None:
        self._storage = storage
        self._llm = llm
        self._feedback_manager = feedback_manager
        self._batch_size = max(1, min(batch_size, 10))
        self._pre_filter_enabled = pre_filter_enabled

    def filter_papers(
        self, papers: list[Paper], interests: dict[str, Any], show_progress: bool = True
    ) -> list[Paper]:
        if not papers:
            return []

        needs_llm, pre_filtered = self._pre_filter(papers, interests)

        for paper in pre_filtered:
            self._apply_and_persist(paper, {
                "score": 1.0, "band": "low",
                "reason": "title pre-filtered", "topics": [],
            })

        if needs_llm:
            self._score_papers(needs_llm, interests, show_progress)

        self._apply_feedback_offset(papers)

        failed = sum(1 for p in papers if p.recommendation_reason == "LLM 评分失败")
        if failed:
            logger.warning("LLM scoring failed for %d/%d papers", failed, len(papers))

        if pre_filtered:
            logger.info(
                "Pre-filtered %d/%d papers, LLM scored %d",
                len(pre_filtered), len(papers), len(needs_llm),
            )

        return sorted(papers, key=lambda p: p.relevance_score, reverse=True)

    def _pre_filter(
        self, papers: list[Paper], interests: dict[str, Any]
    ) -> tuple[list[Paper], list[Paper]]:
        """Split papers into those needing LLM and those pre-filtered out."""
        if not self._pre_filter_enabled:
            return papers, []

        topics = [t.lower() for t in interests.get("topics", [])]
        keywords = [k.lower() for k in interests.get("keywords", [])]
        if not topics and not keywords:
            return papers, []

        match_terms = set(topics + keywords)
        try:
            from paper_agent.services.search_engine import _SYNONYM_GROUPS
            expanded: set[str] = set()
            for term in match_terms:
                for group in _SYNONYM_GROUPS:
                    lower_group = [g.lower() for g in group]
                    if term in lower_group:
                        expanded.update(lower_group)
            match_terms.update(expanded)
        except ImportError:
            pass

        needs_llm: list[Paper] = []
        filtered: list[Paper] = []
        for paper in papers:
            text = (paper.title + " " + paper.abstract[:200]).lower()
            if any(term in text for term in match_terms):
                needs_llm.append(paper)
            else:
                filtered.append(paper)

        return needs_llm, filtered

    def _score_papers(
        self, papers: list[Paper], interests: dict[str, Any], show_progress: bool
    ) -> None:
        """Score papers using batch LLM calls with per-paper fallback."""
        batches = [
            papers[i:i + self._batch_size]
            for i in range(0, len(papers), self._batch_size)
        ]

        all_results: list[tuple[Paper, dict[str, Any]]] = []

        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
            ) as progress:
                task = progress.add_task("Scoring papers...", total=len(papers))
                with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
                    futures = {
                        pool.submit(self._score_batch, batch, interests): batch
                        for batch in batches
                    }
                    for future in as_completed(futures):
                        batch = futures[future]
                        batch_results = future.result()
                        all_results.extend(zip(batch, batch_results))
                        progress.advance(task, len(batch))
        else:
            with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
                futures = {
                    pool.submit(self._score_batch, batch, interests): batch
                    for batch in batches
                }
                for future in as_completed(futures):
                    batch = futures[future]
                    batch_results = future.result()
                    all_results.extend(zip(batch, batch_results))

        for paper, result in all_results:
            self._apply_and_persist(paper, result)

    def _score_batch(
        self, batch: list[Paper], interests: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Score a batch via LLM; fallback to per-paper on failure."""
        if len(batch) == 1:
            return [self._call_llm(batch[0], interests)]

        try:
            results = self._llm.score_relevance_batch(batch, interests)
            has_failure = any(r.get("reason") == "batch解析失败" for r in results)
            if has_failure:
                raise ValueError("batch parse failure detected")
            return results
        except Exception:
            logger.info(
                "Batch scoring failed for %d papers, falling back to per-paper",
                len(batch),
            )
            return [self._call_llm(p, interests) for p in batch]

    def _call_llm(self, paper: Paper, interests: dict[str, Any]) -> dict[str, Any]:
        """Call LLM for single-paper relevance scoring (thread-safe)."""
        try:
            return self._llm.score_relevance(paper, interests)
        except Exception:
            logger.warning("LLM call failed for paper %s, assigning score 0", paper.id)
            return {"score": 0.0, "band": "low", "reason": "LLM 评分失败", "topics": []}

    def _apply_feedback_offset(self, papers: list[Paper]) -> None:
        """Apply feedback-based score offsets. Gracefully degrades if unavailable."""
        if not self._feedback_manager:
            return
        try:
            topic_weights = self._feedback_manager.get_adjusted_topic_weights()
        except Exception:
            logger.warning("FeedbackManager unavailable, skipping preference adjustment")
            return

        if not topic_weights:
            return

        for paper in papers:
            if not paper.topics:
                continue
            matched_offsets = [
                topic_weights[t] for t in paper.topics if t in topic_weights
            ]
            if not matched_offsets:
                continue
            avg_offset = sum(matched_offsets) / len(matched_offsets)
            clamped_offset = max(-2.0, min(2.0, avg_offset))
            paper.relevance_score = max(0.0, min(10.0, paper.relevance_score + clamped_offset))
            paper.relevance_band = "high" if paper.relevance_score >= 7.0 else "low"

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
