"""Semantic Scholar universal paper adapter.

Replaces per-conference adapters (DBLP, OpenReview, ACL Anthology) with a
single unified adapter that searches Semantic Scholar by keywords and
filters by venue names.

API: https://api.semanticscholar.org/graph/v1/paper/search
Rate limit: ~1 req/s without key, higher with S2_API_KEY.
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

S2_API_URL = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = ",".join([
    "title", "abstract", "authors", "venue", "year", "url",
    "externalIds", "citationCount", "openAccessPdf",
    "publicationVenue", "publicationTypes",
])
S2_MAX_PER_REQUEST = 100
S2_REQUEST_DELAY = 1.2
S2_MAX_RETRIES = 3


class SemanticScholarAdapter(SourceAdapter):

    @property
    def api_type(self) -> str:
        return "semantic_scholar"

    @property
    def rate_limit_delay(self) -> float:
        return S2_REQUEST_DELAY

    def __init__(self, api_key: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._api_key = api_key or os.environ.get("S2_API_KEY", "")
        headers: dict[str, str] = {}
        if self._api_key:
            headers["x-api-key"] = self._api_key
        self._client = httpx.Client(
            timeout=30.0, follow_redirects=True, trust_env=True, headers=headers,
        )

    # ── SourceAdapter interface (per-source, used by SourceCollector) ──

    def collect(
        self,
        api_config: dict,
        since: datetime | None = None,
        max_results: int = 200,
    ) -> list[Paper]:
        """Collect from a single venue or keyword query."""
        venue = api_config.get("venue_name") or api_config.get("venue", "")
        query = api_config.get("query", "")
        if not query and not venue:
            return []
        return self._search(
            query=query, venues=[venue] if venue else [], since=since,
            max_results=max_results,
        )

    # ── Profile-driven discovery (the main entry point) ──

    def discover(
        self,
        keywords: list[str],
        venues: list[str] | None = None,
        since: datetime | None = None,
        max_results: int = 100,
    ) -> list[Paper]:
        """Search S2 by profile keywords, filter by enabled venue names.

        This is the primary collection method: instead of crawling each
        conference separately, we search by the user's research interests
        and keep only papers from venues they care about.

        Args:
            keywords: Research topics + keywords from user profile.
            venues: Venue names to keep (e.g. ["DAC", "NeurIPS"]).
                    If empty/None, no venue filter is applied.
            since: Only return papers published on or after this date.
            max_results: Maximum total papers to return.
        """
        if not keywords:
            self._log("SemanticScholar.discover: no keywords, skipping")
            return []

        all_papers: list[Paper] = []
        seen_keys: set[str] = set()

        query_groups = self._build_queries(keywords)
        per_query_limit = max(max_results // max(len(query_groups), 1), 20)

        self._progress(
            f"S2: 搜索 {len(query_groups)} 组关键词, "
            f"venue 过滤={venues or '无'}"
        )

        for i, query in enumerate(query_groups):
            if len(all_papers) >= max_results:
                break

            self._progress(f"S2: 查询 [{i+1}/{len(query_groups)}] \"{query}\" ...")

            papers = self._search(
                query=query,
                venues=venues or [],
                since=since,
                max_results=per_query_limit,
            )

            for p in papers:
                if p.canonical_key not in seen_keys:
                    seen_keys.add(p.canonical_key)
                    all_papers.append(p)

            self._progress(f"S2: 查询 [{i+1}/{len(query_groups)}] 得到 {len(papers)} 篇")

            if len(query_groups) > 1:
                time.sleep(S2_REQUEST_DELAY)

        self._progress(f"S2: 完成, 共 {len(all_papers)} 篇唯一论文")
        self._log(
            f"SemanticScholar.discover: {len(all_papers)} papers "
            f"from {len(query_groups)} queries, venues={venues}"
        )
        return all_papers[:max_results]

    # ── Internal ──

    def _build_queries(self, keywords: list[str]) -> list[str]:
        """Build at most 3 search queries from keywords."""
        if len(keywords) <= 4:
            return [" ".join(keywords)]
        # One broad query + one focused query, max 2-3 total
        queries = [" ".join(keywords[:5])]
        if len(keywords) > 5:
            queries.append(" ".join(keywords[5:10]))
        return queries[:3]

    def _search(
        self,
        query: str,
        venues: list[str],
        since: datetime | None,
        max_results: int,
    ) -> list[Paper]:
        papers: list[Paper] = []
        offset = 0
        retries = 0

        year_param = ""
        if since:
            current_year = datetime.utcnow().year
            year_param = f"{since.year}-{current_year}"

        venue_set = {v.lower() for v in venues} if venues else set()

        while offset < max_results:
            batch_size = min(S2_MAX_PER_REQUEST, max_results - offset)
            params: dict[str, Any] = {
                "query": query,
                "fields": S2_FIELDS,
                "limit": batch_size,
                "offset": offset,
            }
            if year_param:
                params["year"] = year_param

            self._log(
                f"S2 search: query={query!r}, offset={offset}, "
                f"year={year_param}"
            )

            try:
                resp = self._client.get(f"{S2_API_URL}/paper/search", params=params)
            except httpx.HTTPError as e:
                self._log(f"S2 HTTP error: {e}")
                break

            if resp.status_code == 429:
                retries += 1
                if retries > S2_MAX_RETRIES:
                    self._log(f"S2 rate limited, max retries ({S2_MAX_RETRIES}) exceeded, stopping")
                    break
                wait = min(5 * retries, 15)
                self._log(f"S2 rate limited (429), retry {retries}/{S2_MAX_RETRIES}, wait {wait}s")
                time.sleep(wait)
                continue

            if resp.status_code != 200:
                self._log(f"S2 non-200: status={resp.status_code}")
                break

            retries = 0  # reset on success

            try:
                data = resp.json()
            except Exception as e:
                self._log(f"S2 JSON parse error: {e}")
                break

            hits = data.get("data", [])
            if not hits:
                break

            for hit in hits:
                paper = self._parse_hit(hit)
                if not paper:
                    continue
                if venue_set and not self._venue_matches(paper, venue_set):
                    continue
                if since and paper.published_at and paper.published_at < since:
                    continue
                papers.append(paper)

            offset += batch_size
            total = data.get("total", 0)
            if offset >= total:
                break

            time.sleep(S2_REQUEST_DELAY)

        return papers

    def _venue_matches(self, paper: Paper, venue_set: set[str]) -> bool:
        """Check if paper's venue matches any in the filter set."""
        meta = paper.metadata
        paper_venue = str(meta.get("venue", "")).lower()
        pub_venue = str(meta.get("publication_venue_name", "")).lower()

        for v in venue_set:
            vl = v.lower()
            if vl in paper_venue or vl in pub_venue:
                return True
            # Also check topics (which include venue short name)
            for t in paper.topics:
                if vl == t.lower():
                    return True
        return False

    def _parse_hit(self, hit: dict) -> Paper | None:
        title = (hit.get("title") or "").strip()
        if not title:
            return None

        abstract = (hit.get("abstract") or "").strip()

        authors_data = hit.get("authors") or []
        authors = [a.get("name", "") for a in authors_data if a.get("name")]

        year = hit.get("year")
        published_at = datetime(year, 1, 1) if year else None

        url = hit.get("url") or ""

        # External IDs (arXiv, DOI, etc.)
        ext_ids = hit.get("externalIds") or {}
        arxiv_id = ext_ids.get("ArXiv", "")
        doi = ext_ids.get("DOI", "")
        s2_id = hit.get("paperId", "")

        if not url:
            if arxiv_id:
                url = f"https://arxiv.org/abs/{arxiv_id}"
            elif doi:
                url = f"https://doi.org/{doi}"

        # Canonical key: prefer arXiv ID, then DOI, then S2 ID
        if arxiv_id:
            canonical_key = f"arxiv:{arxiv_id}"
        elif doi:
            canonical_key = f"doi:{doi}"
        elif s2_id:
            canonical_key = f"s2:{s2_id}"
        else:
            canonical_key = f"hash:{hashlib.md5(title.encode()).hexdigest()[:16]}"

        venue = hit.get("venue") or ""
        pub_venue_data = hit.get("publicationVenue") or {}
        pub_venue_name = pub_venue_data.get("name", "") if isinstance(pub_venue_data, dict) else ""

        topics: list[str] = []
        if venue:
            topics.append(venue)

        pub_types = hit.get("publicationTypes") or []
        citation_count = hit.get("citationCount") or 0

        pdf_info = hit.get("openAccessPdf") or {}
        pdf_url = pdf_info.get("url", "") if isinstance(pdf_info, dict) else ""

        tldr = hit.get("tldr")
        tldr_text = tldr.get("text", "") if isinstance(tldr, dict) else ""
        influential_count = hit.get("influentialCitationCount", 0)
        fields_of_study = hit.get("fieldsOfStudy") or []

        return Paper(
            canonical_key=canonical_key,
            source_name="semantic_scholar",
            source_paper_id=s2_id,
            title=title,
            abstract=abstract,
            authors=authors,
            published_at=published_at,
            url=url,
            topics=topics,
            doi=doi or None,
            venue=venue,
            citation_count=citation_count if citation_count else None,
            pdf_url=pdf_url or None,
            metadata={
                "s2_id": s2_id,
                "arxiv_id": arxiv_id,
                "doi": doi,
                "venue": venue,
                "publication_venue_name": pub_venue_name,
                "citation_count": citation_count,
                "publication_types": pub_types,
                "pdf_url": pdf_url,
                "tldr": tldr_text,
                "influential_citation_count": influential_count,
                "fields_of_study": fields_of_study,
            },
        )
