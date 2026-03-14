"""Concurrent multi-source paper collection scheduler.

Groups enabled sources by api_type and fetches each group in parallel
using a thread pool. Within each group, sources are queried serially
to respect per-API rate limits.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from paper_agent.domain.models.paper import Paper
from paper_agent.infra.sources.base_adapter import SourceAdapter
from paper_agent.infra.sources.source_registry import SourceDefinition


@dataclass
class SourceCollectionResult:
    """Result from collecting across all sources."""
    papers: list[Paper] = field(default_factory=list)
    source_stats: dict[str, dict[str, int]] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def total_collected(self) -> int:
        return len(self.papers)


class SourceCollector:
    """Dispatches collection requests to the appropriate adapter, concurrently."""

    def __init__(
        self,
        adapters: dict[str, SourceAdapter] | None = None,
        debug: bool = False,
        debug_log: Callable[[str], None] | None = None,
        max_workers: int = 4,
    ) -> None:
        self._adapters: dict[str, SourceAdapter] = adapters or {}
        self._debug = debug
        self._debug_log = debug_log
        self._max_workers = max_workers

    def _log(self, message: str) -> None:
        if self._debug and self._debug_log is not None:
            self._debug_log(message)

    def register_adapter(self, adapter: SourceAdapter) -> None:
        self._adapters[adapter.api_type] = adapter

    def collect_all(
        self,
        sources: list[SourceDefinition],
        since: datetime | None = None,
        max_results: int = 200,
    ) -> SourceCollectionResult:
        result = SourceCollectionResult()

        # Group sources by api_type for concurrent execution
        groups: dict[str, list[SourceDefinition]] = {}
        for src in sources:
            if not src.enabled:
                continue
            groups.setdefault(src.api_type, []).append(src)

        self._log(
            f"SourceCollector: {len(sources)} sources, "
            f"{sum(1 for s in sources if s.enabled)} enabled, "
            f"{len(groups)} api_type groups: {list(groups.keys())}"
        )

        if not groups:
            return result

        # Each api_type group runs in its own thread; within a group, serial
        num_workers = min(self._max_workers, len(groups))
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(
                    self._collect_group, api_type, group_sources, since, max_results
                ): api_type
                for api_type, group_sources in groups.items()
            }

            for future in as_completed(futures):
                api_type = futures[future]
                try:
                    group_papers, group_stats, group_errors = future.result()
                    result.papers.extend(group_papers)
                    result.source_stats.update(group_stats)
                    result.errors.update(group_errors)
                    self._log(
                        f"SourceCollector: group={api_type} done, "
                        f"papers={len(group_papers)}"
                    )
                except Exception as e:
                    self._log(f"SourceCollector: group={api_type} failed: {e}")
                    result.errors[api_type] = str(e)

        self._log(f"SourceCollector: total={result.total_collected} papers collected")
        return result

    def _collect_group(
        self,
        api_type: str,
        sources: list[SourceDefinition],
        since: datetime | None,
        max_results: int,
    ) -> tuple[list[Paper], dict[str, dict[str, int]], dict[str, str]]:
        adapter = self._adapters.get(api_type)
        if not adapter:
            self._log(f"No adapter registered for api_type={api_type}")
            return [], {}, {api_type: f"No adapter for {api_type}"}

        all_papers: list[Paper] = []
        stats: dict[str, dict[str, int]] = {}
        errors: dict[str, str] = {}

        for i, src in enumerate(sources):
            self._log(f"Collecting source={src.id} ({src.display_name})")
            try:
                papers = adapter.collect(
                    api_config=src.api_config or {},
                    since=since,
                    max_results=max_results,
                )
                all_papers.extend(papers)
                stats[src.id] = {"collected": len(papers)}
                self._log(
                    f"Source {src.id}: collected {len(papers)} papers"
                )
            except Exception as e:
                self._log(f"Source {src.id} failed: {e}")
                errors[src.id] = str(e)
                stats[src.id] = {"collected": 0, "error": 1}

            # Rate limiting between sources within the same API
            if i < len(sources) - 1:
                delay = adapter.rate_limit_delay
                self._log(f"Sleeping {delay}s before next source in {api_type}")
                time.sleep(delay)

        return all_papers, stats, errors
