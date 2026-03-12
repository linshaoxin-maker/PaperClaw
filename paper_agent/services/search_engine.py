"""Search engine: FTS5-based retrieval with ranking."""

from __future__ import annotations

from paper_agent.domain.models.paper import Paper
from paper_agent.domain.models.query_result import QueryResult
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage


class SearchEngine:
    def __init__(self, storage: SQLiteStorage) -> None:
        self._storage = storage

    def search(
        self, query: str, limit: int = 50, mode: str = "retrieval"
    ) -> QueryResult:
        papers = self._storage.search_papers(query, limit=limit)
        return QueryResult(
            query=query,
            mode=mode,
            papers=papers,
            status="completed" if papers else "empty",
        )

    def rank_results(self, papers: list[Paper], query: str) -> list[Paper]:
        return sorted(papers, key=lambda p: p.relevance_score, reverse=True)
