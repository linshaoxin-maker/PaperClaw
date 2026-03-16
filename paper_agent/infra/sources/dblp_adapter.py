"""DBLP paper collection adapter.

Uses the DBLP search API to fetch papers from conferences like
DAC, ICCAD, DATE, ISCA, CVPR, ICCV, ECCV, AAAI, IJCAI, etc.

API docs: https://dblp.org/faq/How+to+use+the+dblp+search+API.html
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

import httpx

from paper_agent.domain.models.paper import Paper
from paper_agent.infra.sources.base_adapter import SourceAdapter

DBLP_SEARCH_URL = "https://dblp.org/search/publ/api"
DBLP_VENUE_URL = "https://dblp.org/search/venue/api"


class DBLPAdapter(SourceAdapter):

    @property
    def api_type(self) -> str:
        return "dblp"

    @property
    def rate_limit_delay(self) -> float:
        return 1.0

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._client = httpx.Client(timeout=30.0, follow_redirects=True, trust_env=True)

    def collect(
        self,
        api_config: dict,
        since: datetime | None = None,
        max_results: int = 200,
    ) -> list[Paper]:
        venue_key = api_config.get("venue_key", "")
        if not venue_key:
            self._log("DBLPAdapter: no venue_key in api_config, skipping")
            return []

        since_year = since.year if since else datetime.utcnow().year
        self._progress(f"DBLP: 查询 {venue_key} (since {since_year}) ...")
        return self._query_venue(venue_key, since_year, max_results)

    def _query_venue(
        self, venue_key: str, since_year: int, max_results: int
    ) -> list[Paper]:
        """Search DBLP for papers from a venue published since `since_year`."""
        papers: list[Paper] = []
        offset = 0
        batch_size = min(100, max_results)

        while offset < max_results:
            params: dict[str, Any] = {
                "q": f"stream:streams/{venue_key}:",
                "format": "json",
                "h": batch_size,
                "f": offset,
            }
            self._log(f"DBLP request: venue={venue_key}, offset={offset}, params={params}")

            try:
                resp = self._client.get(DBLP_SEARCH_URL, params=params)
            except httpx.HTTPError as e:
                self._log(f"DBLP HTTP error: {e}")
                break

            if resp.status_code != 200:
                self._log(f"DBLP non-200: status={resp.status_code}")
                break

            try:
                data = resp.json()
            except Exception as e:
                self._log(f"DBLP JSON parse error: {e}")
                break

            result = data.get("result", {})
            hits = result.get("hits", {})
            hit_list = hits.get("hit", [])

            if not hit_list:
                self._log(f"DBLP: no more hits for venue={venue_key}")
                break

            for hit in hit_list:
                info = hit.get("info", {})
                paper = self._parse_hit(info, venue_key)
                if not paper:
                    continue
                if paper.published_at and paper.published_at.year < since_year:
                    self._log(
                        f"DBLP: stopping at year {paper.published_at.year} "
                        f"< {since_year}"
                    )
                    return papers
                papers.append(paper)

            offset += batch_size
            total_str = hits.get("@total", "0")
            total = int(total_str) if total_str.isdigit() else 0
            if offset >= total:
                break

        self._progress(f"DBLP: {venue_key} 完成, {len(papers)} 篇")
        self._log(f"DBLP: collected {len(papers)} papers from {venue_key}")
        return papers

    def _parse_hit(self, info: dict, venue_key: str) -> Paper | None:
        title = info.get("title", "").strip().rstrip(".")
        if not title:
            return None

        authors_data = info.get("authors", {}).get("author", [])
        if isinstance(authors_data, dict):
            authors_data = [authors_data]
        authors = []
        for a in authors_data:
            name = a.get("text", "") if isinstance(a, dict) else str(a)
            if name:
                authors.append(name)

        year_str = info.get("year", "")
        published_at = None
        if year_str:
            try:
                published_at = datetime(int(year_str), 1, 1)
            except (ValueError, TypeError):
                pass

        url = info.get("ee", "") or info.get("url", "")
        if isinstance(url, list):
            url = url[0] if url else ""

        dblp_key = info.get("key", "")
        venue_name = info.get("venue", "")
        if isinstance(venue_name, list):
            venue_name = venue_name[0] if venue_name else ""

        canonical_key = (
            f"dblp:{dblp_key}"
            if dblp_key
            else f"hash:{hashlib.md5(title.encode()).hexdigest()[:16]}"
        )

        conf_short = venue_key.split("/")[-1].upper() if "/" in venue_key else venue_key.upper()

        # Extract DOI from DBLP
        doi = info.get("doi", "")
        if isinstance(doi, list):
            doi = doi[0] if doi else ""

        return Paper(
            canonical_key=canonical_key,
            source_name="dblp",
            source_paper_id=dblp_key,
            title=title,
            abstract="",
            authors=authors,
            published_at=published_at,
            url=url,
            topics=[conf_short],
            doi=doi or None,
            venue=venue_name,
            metadata={
                "dblp_key": dblp_key,
                "venue": venue_name,
                "venue_key": venue_key,
                "doi": doi,
            },
        )
