"""Watchlist service: long-term tracking of topics, authors, venues, and citations."""

from __future__ import annotations

from typing import Any

from paper_agent.domain.models.paper import Paper
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage


class WatchlistManager:
    def __init__(self, storage: SQLiteStorage) -> None:
        self._storage = storage

    def add_watch(
        self,
        watch_type: str,
        watch_value: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Add a watchlist item.

        watch_type: "topic" | "author" | "venue" | "method_line" | "forward_citations"
        watch_value: the value to track (e.g. topic name, author name, paper_id for citations)
        """
        valid_types = {"topic", "author", "venue", "method_line", "forward_citations"}
        if watch_type not in valid_types:
            return {"error": f"Invalid watch_type. Use: {sorted(valid_types)}"}

        watch_id = self._storage.save_watchlist_item(watch_type, watch_value, description)
        return {
            "status": "ok",
            "watch_id": watch_id,
            "type": watch_type,
            "value": watch_value,
            "description": description,
        }

    def list_watches(self) -> list[dict[str, Any]]:
        """List all watchlist items."""
        return self._storage.list_watchlist_items()

    def remove_watch(self, watch_id: str) -> dict[str, Any]:
        """Remove a watchlist item."""
        self._storage.delete_watchlist_item(watch_id)
        return {"status": "ok", "deleted": watch_id}

    def check_updates(self, watch_id: str | None = None) -> dict[str, Any]:
        """Check for new papers matching watchlist criteria.

        If watch_id is provided, checks only that item.
        Otherwise checks all items.
        """
        items = self._storage.list_watchlist_items()
        if watch_id:
            items = [w for w in items if w["id"] == watch_id]

        results: list[dict[str, Any]] = []

        for item in items:
            new_papers = self._check_single(item)
            if new_papers:
                results.append({
                    "watch_id": item["id"],
                    "type": item["watch_type"],
                    "value": item["watch_value"],
                    "new_count": len(new_papers),
                    "papers": [
                        {"id": p.id, "title": p.title, "score": p.relevance_score}
                        for p in new_papers[:10]
                    ],
                })
                self._storage.update_watchlist_checked(item["id"])

        return {
            "status": "ok",
            "checked": len(items),
            "with_updates": len(results),
            "results": results,
        }

    def generate_digest(self) -> dict[str, Any]:
        """Generate a digest of all watchlist updates since last check."""
        updates = self.check_updates()
        results = updates.get("results", [])

        if not results:
            return {"status": "ok", "message": "没有新的 watchlist 更新。", "items": []}

        digest_items: list[dict[str, Any]] = []
        for r in results:
            digest_items.append({
                "type": r["type"],
                "value": r["value"],
                "new_count": r["new_count"],
                "top_papers": r["papers"][:5],
            })

        return {
            "status": "ok",
            "total_updates": sum(r["new_count"] for r in results),
            "items": digest_items,
        }

    def _check_single(self, item: dict[str, Any]) -> list[Paper]:
        """Check for new papers matching a single watchlist item."""
        watch_type = item["watch_type"]
        watch_value = item["watch_value"]
        last_checked = item.get("last_checked")

        if watch_type == "topic":
            return self._storage.search_papers(watch_value, limit=20)

        elif watch_type == "author":
            all_papers = self._storage.get_all_papers(limit=5000)
            return [
                p for p in all_papers
                if any(watch_value.lower() in a.lower() for a in p.authors)
            ]

        elif watch_type == "venue":
            all_papers = self._storage.get_all_papers(limit=5000)
            return [
                p for p in all_papers
                if watch_value.lower() in (p.metadata.get("venue", "") or "").lower()
                or watch_value.lower() in p.source_name.lower()
            ]

        elif watch_type == "method_line":
            return self._storage.search_papers(watch_value, limit=20)

        elif watch_type == "forward_citations":
            from paper_agent.services.citation_service import CitationService
            cit_service = CitationService(self._storage)
            result = cit_service.get_citations(watch_value, direction="citations", limit=20)
            paper_ids = [c.get("id", "") for c in result.get("citations", []) if c.get("id")]
            return [p for pid in paper_ids if (p := self._storage.get_paper(pid))]

        return []
