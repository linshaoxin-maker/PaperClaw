"""OpenAlex paper collection adapter.

OpenAlex is a free, open academic graph indexing 250M+ scholarly works.
No API key required (polite pool with mailto).

API docs: https://docs.openalex.org/
"""

from __future__ import annotations

import hashlib
import os
import time
from datetime import datetime
from typing import Any

import httpx

from paper_agent.domain.models.paper import Paper
from paper_agent.infra.sources.base_adapter import SourceAdapter

OPENALEX_API_URL = "https://api.openalex.org"
OPENALEX_REQUEST_DELAY = 0.2
OPENALEX_MAX_PER_PAGE = 100


class OpenAlexAdapter(SourceAdapter):

    @property
    def api_type(self) -> str:
        return "openalex"

    @property
    def rate_limit_delay(self) -> float:
        return OPENALEX_REQUEST_DELAY

    def __init__(self, mailto: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._mailto = mailto or os.environ.get("OPENALEX_MAILTO", "")
        headers: dict[str, str] = {"User-Agent": "paper-agent/1.0"}
        self._client = httpx.Client(
            timeout=30.0, follow_redirects=True, trust_env=True, headers=headers,
        )

    def collect(
        self,
        api_config: dict,
        since: datetime | None = None,
        max_results: int = 200,
    ) -> list[Paper]:
        query = api_config.get("query", "")
        venue_id = api_config.get("venue_id", "")
        if not query and not venue_id:
            return []
        return self._search(
            query=query, venue_id=venue_id, since=since, max_results=max_results,
        )

    def discover(
        self,
        keywords: list[str],
        venues: list[str] | None = None,
        since: datetime | None = None,
        max_results: int = 100,
    ) -> list[Paper]:
        """Keyword-based discovery with optional venue filtering."""
        if not keywords:
            self._log("OpenAlex.discover: no keywords, skipping")
            return []

        all_papers: list[Paper] = []
        seen_keys: set[str] = set()

        queries = self._build_queries(keywords)
        per_query = max(max_results // max(len(queries), 1), 20)

        self._progress(f"OpenAlex: 搜索 {len(queries)} 组关键词 ...")

        for i, query in enumerate(queries):
            if len(all_papers) >= max_results:
                break

            papers = self._search(
                query=query, since=since, max_results=per_query,
            )

            for p in papers:
                if p.canonical_key not in seen_keys:
                    if venues and not self._venue_matches(p, venues):
                        continue
                    seen_keys.add(p.canonical_key)
                    all_papers.append(p)

            self._progress(f"OpenAlex: 查询 [{i+1}/{len(queries)}] 得到 {len(papers)} 篇")

            if len(queries) > 1:
                time.sleep(OPENALEX_REQUEST_DELAY)

        self._progress(f"OpenAlex: 完成, 共 {len(all_papers)} 篇唯一论文")
        return all_papers[:max_results]

    def _build_queries(self, keywords: list[str]) -> list[str]:
        if len(keywords) <= 4:
            return [" ".join(keywords)]
        queries = [" ".join(keywords[:5])]
        if len(keywords) > 5:
            queries.append(" ".join(keywords[5:10]))
        return queries[:3]

    def _search(
        self,
        query: str = "",
        venue_id: str = "",
        since: datetime | None = None,
        max_results: int = 100,
    ) -> list[Paper]:
        papers: list[Paper] = []
        cursor = "*"

        while len(papers) < max_results and cursor:
            params: dict[str, Any] = {
                "per_page": min(OPENALEX_MAX_PER_PAGE, max_results - len(papers)),
                "cursor": cursor,
                "select": "id,doi,title,display_name,publication_date,authorships,"
                          "primary_location,open_access,cited_by_count,"
                          "concepts,topics,abstract_inverted_index",
            }

            filters: list[str] = []
            if since:
                filters.append(f"from_publication_date:{since.strftime('%Y-%m-%d')}")
            filters.append("type:article|proceedings-article|preprint|posted-content")

            if venue_id:
                filters.append(f"primary_location.source.id:{venue_id}")

            if filters:
                params["filter"] = ",".join(filters)

            if query:
                params["search"] = query

            if self._mailto:
                params["mailto"] = self._mailto

            self._log(f"OpenAlex request: query={query!r}, cursor={cursor[:20]}...")

            try:
                resp = self._client.get(f"{OPENALEX_API_URL}/works", params=params)
            except httpx.HTTPError as e:
                self._log(f"OpenAlex HTTP error: {e}")
                break

            if resp.status_code == 429:
                self._log("OpenAlex rate limited, waiting 2s")
                time.sleep(2.0)
                continue

            if resp.status_code != 200:
                self._log(f"OpenAlex non-200: status={resp.status_code}")
                break

            try:
                data = resp.json()
            except Exception:
                break

            results = data.get("results", [])
            if not results:
                break

            for work in results:
                paper = self._parse_work(work)
                if paper:
                    papers.append(paper)

            meta = data.get("meta", {})
            cursor = meta.get("next_cursor")
            if not cursor:
                break

            time.sleep(OPENALEX_REQUEST_DELAY)

        return papers

    def _venue_matches(self, paper: Paper, venues: list[str]) -> bool:
        venue_set = {v.lower() for v in venues}
        meta = paper.metadata
        source_name = str(meta.get("source_name", "")).lower()
        for v in venue_set:
            if v in source_name:
                return True
            for t in paper.topics:
                if v == t.lower():
                    return True
        return False

    def _parse_work(self, work: dict) -> Paper | None:
        title = (work.get("display_name") or work.get("title") or "").strip()
        if not title:
            return None

        abstract = self._reconstruct_abstract(work.get("abstract_inverted_index"))

        authorships = work.get("authorships") or []
        authors = [
            a.get("author", {}).get("display_name", "")
            for a in authorships
            if a.get("author", {}).get("display_name")
        ]

        pub_date = work.get("publication_date")
        published_at = None
        if pub_date:
            try:
                published_at = datetime.strptime(pub_date, "%Y-%m-%d")
            except (ValueError, TypeError):
                try:
                    published_at = datetime.strptime(pub_date[:4], "%Y")
                except (ValueError, TypeError):
                    pass

        doi = work.get("doi") or ""
        if doi and doi.startswith("https://doi.org/"):
            doi = doi[len("https://doi.org/"):]

        openalex_id = work.get("id", "")
        url = doi and f"https://doi.org/{doi}" or openalex_id or ""

        primary_loc = work.get("primary_location") or {}
        source = primary_loc.get("source") or {}
        source_display = source.get("display_name", "")

        oa_info = work.get("open_access") or {}
        oa_url = oa_info.get("oa_url", "")

        ext_ids: dict[str, str] = {}
        if doi:
            ext_ids["doi"] = doi
        loc_landing = primary_loc.get("landing_page_url", "")
        if "arxiv.org" in (loc_landing or ""):
            arxiv_id = loc_landing.split("/abs/")[-1] if "/abs/" in loc_landing else ""
            if arxiv_id:
                ext_ids["arxiv_id"] = arxiv_id

        if ext_ids.get("arxiv_id"):
            canonical_key = f"arxiv:{ext_ids['arxiv_id']}"
        elif doi:
            canonical_key = f"doi:{doi}"
        elif openalex_id:
            canonical_key = f"openalex:{openalex_id.split('/')[-1]}"
        else:
            canonical_key = f"hash:{hashlib.md5(title.encode()).hexdigest()[:16]}"

        topics: list[str] = []
        if source_display:
            topics.append(source_display)
        for concept in (work.get("concepts") or [])[:3]:
            name = concept.get("display_name", "")
            if name and name not in topics:
                topics.append(name)

        citation_count = work.get("cited_by_count") or 0

        if not url and loc_landing:
            url = loc_landing

        # Extract author affiliations
        affiliations = []
        for authorship in work.get("authorships", []):
            inst_list = authorship.get("institutions", [])
            for inst in inst_list:
                inst_name = inst.get("display_name", "")
                if inst_name and inst_name not in affiliations:
                    affiliations.append(inst_name)

        return Paper(
            canonical_key=canonical_key,
            source_name="openalex",
            source_paper_id=openalex_id.split("/")[-1] if openalex_id else "",
            title=title,
            abstract=abstract,
            authors=authors,
            published_at=published_at,
            url=url,
            topics=topics,
            doi=doi or None,
            venue=source_display,
            citation_count=citation_count if citation_count else None,
            pdf_url=oa_url or None,
            metadata={
                "openalex_id": openalex_id,
                "doi": doi,
                "arxiv_id": ext_ids.get("arxiv_id", ""),
                "source_name": source_display,
                "citation_count": citation_count,
                "oa_url": oa_url,
                "affiliations": affiliations[:10],
            },
        )

    @staticmethod
    def _reconstruct_abstract(inverted_index: dict | None) -> str:
        """Reconstruct abstract from OpenAlex inverted index format."""
        if not inverted_index or not isinstance(inverted_index, dict):
            return ""
        word_positions: list[tuple[int, str]] = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort(key=lambda x: x[0])
        return " ".join(w for _, w in word_positions)
