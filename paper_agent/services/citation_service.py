"""Citation chain tracking via Semantic Scholar API."""

from __future__ import annotations

import hashlib
import os
import time
import uuid
from datetime import datetime
from typing import Any

import httpx

from paper_agent.domain.models.paper import Paper
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage

S2_API = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = "title,abstract,authors,venue,year,url,externalIds"
_DELAY = 1.2


class CitationService:
    """Queries Semantic Scholar for citation relationships."""

    def __init__(self, storage: SQLiteStorage) -> None:
        self._storage = storage
        self._api_key = os.environ.get("S2_API_KEY", "")

    def get_citations(
        self,
        paper_id: str,
        direction: str = "both",
        limit: int = 20,
    ) -> dict[str, Any]:
        paper = self._storage.get_paper(paper_id)
        if not paper:
            return {"error": f"Paper {paper_id} not found in local database"}

        s2_id = self._resolve_s2_id(paper)
        if not s2_id:
            return {"error": f"Cannot resolve Semantic Scholar ID for '{paper.title}'"}

        result: dict[str, Any] = {
            "paper_id": paper_id,
            "title": paper.title,
            "references": [],
            "citations": [],
        }

        headers = self._headers()

        if direction in ("both", "references"):
            refs = self._fetch_connections(s2_id, "references", limit, headers)
            result["references"] = refs
            self._save_new_papers(refs)

        if direction in ("both", "citations"):
            cites = self._fetch_connections(s2_id, "citations", limit, headers)
            result["citations"] = cites
            self._save_new_papers(cites)

        return result

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {}
        if self._api_key:
            h["x-api-key"] = self._api_key
        return h

    def _resolve_s2_id(self, paper: Paper) -> str | None:
        meta = paper.metadata or {}
        if meta.get("s2_paper_id"):
            return meta["s2_paper_id"]

        arxiv_id = meta.get("arxiv_id") or ""
        if not arxiv_id and paper.source_name == "arxiv" and paper.source_paper_id:
            arxiv_id = paper.source_paper_id

        if arxiv_id:
            return f"ARXIV:{arxiv_id}"

        if paper.url and "doi.org" in paper.url:
            doi = paper.url.split("doi.org/")[-1]
            return f"DOI:{doi}"

        return self._search_by_title(paper.title)

    def _search_by_title(self, title: str) -> str | None:
        try:
            resp = httpx.get(
                f"{S2_API}/paper/search",
                params={"query": title, "limit": 1, "fields": "paperId,title"},
                headers=self._headers(),
                timeout=15.0,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data:
                    return data[0]["paperId"]
        except httpx.HTTPError:
            pass
        return None

    def _fetch_connections(
        self, s2_id: str, kind: str, limit: int, headers: dict
    ) -> list[dict[str, str]]:
        url = f"{S2_API}/paper/{s2_id}/{kind}"
        fields = "title,authors,venue,year,url,externalIds"
        results: list[dict[str, str]] = []
        try:
            time.sleep(_DELAY)
            resp = httpx.get(
                url,
                params={"fields": fields, "limit": min(limit, 100)},
                headers=headers,
                timeout=30.0,
            )
            if resp.status_code != 200:
                return results

            items = resp.json().get("data", [])
            for item in items[:limit]:
                cited = item.get("citedPaper") or item.get("citingPaper") or {}
                if not cited.get("title"):
                    continue
                authors = [a.get("name", "") for a in (cited.get("authors") or [])[:5]]
                ext = cited.get("externalIds") or {}
                entry: dict[str, str] = {
                    "title": cited["title"],
                    "authors": ", ".join(authors),
                    "venue": cited.get("venue", ""),
                    "year": str(cited.get("year", "")),
                    "url": cited.get("url", ""),
                    "arxiv_id": ext.get("ArXiv", ""),
                    "s2_id": cited.get("paperId", ""),
                }
                results.append(entry)
        except httpx.HTTPError:
            pass
        return results

    def trace(
        self,
        paper_id: str,
        direction: str = "both",
        max_depth: int = 2,
        limit_per_level: int = 10,
    ) -> dict[str, Any]:
        """Recursive citation trace up to *max_depth* levels.

        Returns a tree structure with discovered papers at each level,
        auto-saving new papers to the local library.
        """
        paper = self._storage.get_paper(paper_id)
        if not paper:
            return {"error": f"Paper {paper_id} not found in local database"}

        s2_id = self._resolve_s2_id(paper)
        if not s2_id:
            return {"error": f"Cannot resolve Semantic Scholar ID for '{paper.title}'"}

        seed = {"id": paper.id, "title": paper.title, "year": str(paper.published_at.year) if paper.published_at else ""}
        levels: list[dict[str, Any]] = []
        total_discovered = 0
        new_saved = 0

        current_s2_ids: list[tuple[str, str]] = [(s2_id, paper.title)]

        headers = self._headers()

        for depth in range(1, max_depth + 1):
            level_papers: list[dict[str, Any]] = []
            next_s2_ids: list[tuple[str, str]] = []

            for parent_s2_id, parent_title in current_s2_ids[:limit_per_level]:
                if direction in ("both", "references"):
                    refs = self._fetch_connections(parent_s2_id, "references", limit_per_level, headers)
                    self._save_new_papers(refs)
                    new_saved += len(refs)
                    for r in refs:
                        entry = {**r, "direction": "reference", "parent": parent_title}
                        level_papers.append(entry)
                        if r.get("s2_id"):
                            next_s2_ids.append((r["s2_id"], r["title"]))

                if direction in ("both", "citations"):
                    cites = self._fetch_connections(parent_s2_id, "citations", limit_per_level, headers)
                    self._save_new_papers(cites)
                    new_saved += len(cites)
                    for c in cites:
                        entry = {**c, "direction": "cited_by", "parent": parent_title}
                        level_papers.append(entry)
                        if c.get("s2_id"):
                            next_s2_ids.append((c["s2_id"], c["title"]))

            seen_titles: set[str] = set()
            deduped: list[dict[str, Any]] = []
            for p in level_papers:
                t = p["title"].lower().strip()
                if t not in seen_titles:
                    seen_titles.add(t)
                    deduped.append(p)

            total_discovered += len(deduped)
            levels.append({"depth": depth, "count": len(deduped), "papers": deduped[:limit_per_level * 2]})
            current_s2_ids = next_s2_ids

            if not next_s2_ids:
                break

        return {
            "seed": seed,
            "levels": levels,
            "total_discovered": total_discovered,
            "new_saved": new_saved,
            "depth_reached": len(levels),
        }

    def _save_new_papers(self, entries: list[dict[str, str]]) -> None:
        for e in entries:
            if not e.get("title"):
                continue
            raw = (e.get("arxiv_id") or e.get("s2_id") or e["title"]).lower().strip()
            canonical = f"citation:{hashlib.md5(raw.encode()).hexdigest()[:16]}"
            existing = self._storage.get_paper_by_canonical(canonical)
            if existing:
                continue

            year_str = e.get("year", "")
            pub_dt = None
            if year_str and year_str.isdigit():
                pub_dt = datetime(int(year_str), 1, 1)

            p = Paper(
                id=uuid.uuid4().hex[:12],
                canonical_key=canonical,
                source_name="semantic_scholar",
                source_paper_id=e.get("s2_id", ""),
                title=e["title"],
                authors=e.get("authors", "").split(", ") if e.get("authors") else [],
                published_at=pub_dt,
                url=e.get("url", ""),
                metadata={"s2_paper_id": e.get("s2_id", ""), "arxiv_id": e.get("arxiv_id", "")},
            )
            self._storage.save_paper(p)
