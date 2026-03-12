"""Collection service: orchestrate paper ingestion from sources."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from paper_agent.domain.models.collection import CollectionRecord
from paper_agent.domain.models.paper import Paper
from paper_agent.infra.sources.arxiv_adapter import ArxivAdapter
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage


class CollectionManager:
    def __init__(
        self,
        storage: SQLiteStorage,
        debug: bool = False,
        debug_log: Callable[[str], None] | None = None,
    ) -> None:
        self._storage = storage
        self._debug = debug
        self._debug_log = debug_log
        self._arxiv = ArxivAdapter(debug=debug, debug_log=debug_log)

    def _log(self, message: str) -> None:
        if self._debug and self._debug_log is not None:
            self._debug_log(message)

    def collect_from_arxiv(
        self,
        categories: list[str],
        days_back: int = 7,
        max_results: int = 200,
    ) -> CollectionRecord:
        since = datetime.now(timezone.utc) - timedelta(days=days_back)
        record = CollectionRecord(source_name="arxiv", trigger_type="manual")

        self._log(
            f"Collection request received: categories={categories}, days_back={days_back}, max_results={max_results}, since={since.isoformat()}"
        )

        try:
            papers = self._arxiv.collect_papers(
                categories=categories, since=since, max_results=max_results
            )
            record.collected_count = len(papers)
            self._log(f"Fetched papers: collected_count={record.collected_count}")
            new_count, dup_count = self._storage.save_papers(papers)
            record.new_count = new_count
            record.duplicate_count = dup_count
            self._log(
                f"Saved papers: new_count={record.new_count}, duplicate_count={record.duplicate_count}"
            )
            record.status = "completed"
        except Exception as e:
            record.status = "failed"
            record.error_summary = {"error": str(e)}
            self._log(f"Collection failed: error={e}")

        record.finished_at = datetime.utcnow()
        self._storage.save_collection(record)
        self._log(
            f"Collection record saved: status={record.status}, collected_count={record.collected_count}, new_count={record.new_count}, duplicate_count={record.duplicate_count}"
        )
        return record

    def add_paper_by_id(self, arxiv_id: str) -> Paper | None:
        paper = self._arxiv.get_paper_metadata(arxiv_id)
        if paper:
            self._storage.save_paper(paper)
        return paper
