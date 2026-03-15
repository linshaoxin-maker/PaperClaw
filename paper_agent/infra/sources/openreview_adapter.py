"""OpenReview paper collection adapter.

Fetches accepted papers from venues hosted on OpenReview
(NeurIPS, ICML, ICLR, etc.) via the OpenReview API v2.

API docs: https://docs.openreview.net/reference/api-v2
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

import httpx

from paper_agent.domain.models.paper import Paper
from paper_agent.infra.sources.base_adapter import SourceAdapter

OPENREVIEW_API_URL = "https://api2.openreview.net"


class OpenReviewAdapter(SourceAdapter):

    @property
    def api_type(self) -> str:
        return "openreview"

    @property
    def rate_limit_delay(self) -> float:
        return 1.5

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._client = httpx.Client(timeout=30.0, follow_redirects=True, trust_env=True)

    def collect(
        self,
        api_config: dict,
        since: datetime | None = None,
        max_results: int = 200,
    ) -> list[Paper]:
        venue_id = api_config.get("venue_id", "")
        if not venue_id:
            self._log("OpenReviewAdapter: no venue_id in api_config, skipping")
            return []

        since_year = since.year if since else datetime.utcnow().year
        return self._query_venue(venue_id, since_year, max_results)

    def _query_venue(
        self, venue_id: str, since_year: int, max_results: int
    ) -> list[Paper]:
        """Fetch papers from an OpenReview venue for recent years."""
        all_papers: list[Paper] = []
        current_year = datetime.utcnow().year

        for year in range(current_year, since_year - 1, -1):
            if len(all_papers) >= max_results:
                break
            papers = self._fetch_year(venue_id, year, max_results - len(all_papers))
            all_papers.extend(papers)
            if not papers:
                continue

        self._log(f"OpenReview: collected {len(all_papers)} from {venue_id}")
        return all_papers

    def _fetch_year(
        self, venue_id: str, year: int, max_results: int
    ) -> list[Paper]:
        # OpenReview v2 uses different invitation formats; try common patterns
        invitation_patterns = [
            f"{venue_id}/{year}/Conference/-/Submission",
            f"{venue_id}/{year}/Conference/-/Blind_Submission",
        ]

        for invitation in invitation_patterns:
            papers = self._try_invitation(invitation, venue_id, year, max_results)
            if papers:
                return papers

        # Fallback: search by venue content field
        return self._search_by_venue(venue_id, year, max_results)

    def _try_invitation(
        self, invitation: str, venue_id: str, year: int, max_results: int
    ) -> list[Paper]:
        papers: list[Paper] = []
        offset = 0
        batch_size = min(100, max_results)

        while offset < max_results:
            params: dict[str, Any] = {
                "invitation": invitation,
                "limit": batch_size,
                "offset": offset,
            }
            self._log(f"OpenReview request: invitation={invitation}, offset={offset}")

            try:
                resp = self._client.get(f"{OPENREVIEW_API_URL}/notes", params=params)
            except httpx.HTTPError as e:
                self._log(f"OpenReview HTTP error: {e}")
                return papers

            if resp.status_code != 200:
                self._log(f"OpenReview non-200: status={resp.status_code}")
                return papers

            try:
                data = resp.json()
            except Exception:
                return papers

            notes = data.get("notes", [])
            if not notes:
                break

            for note in notes:
                paper = self._parse_note(note, venue_id, year)
                if paper:
                    papers.append(paper)

            offset += batch_size
            if len(notes) < batch_size:
                break

        return papers

    def _search_by_venue(
        self, venue_id: str, year: int, max_results: int
    ) -> list[Paper]:
        """Fallback: search OpenReview notes by venue content field."""
        params: dict[str, Any] = {
            "content.venue": f"{venue_id} {year}",
            "limit": min(100, max_results),
            "offset": 0,
        }
        self._log(f"OpenReview venue search: venue_id={venue_id}, year={year}")

        try:
            resp = self._client.get(f"{OPENREVIEW_API_URL}/notes", params=params)
        except httpx.HTTPError as e:
            self._log(f"OpenReview search error: {e}")
            return []

        if resp.status_code != 200:
            return []

        try:
            data = resp.json()
        except Exception:
            return []

        papers: list[Paper] = []
        for note in data.get("notes", []):
            paper = self._parse_note(note, venue_id, year)
            if paper:
                papers.append(paper)
        return papers

    def _parse_note(self, note: dict, venue_id: str, year: int) -> Paper | None:
        content = note.get("content", {})

        title_field = content.get("title", {})
        title = title_field.get("value", "") if isinstance(title_field, dict) else str(title_field)
        title = title.strip()
        if not title:
            return None

        abstract_field = content.get("abstract", {})
        abstract = (
            abstract_field.get("value", "")
            if isinstance(abstract_field, dict)
            else str(abstract_field)
        ).strip()

        authors_field = content.get("authors", {})
        authors_list = (
            authors_field.get("value", [])
            if isinstance(authors_field, dict)
            else authors_field
        )
        if isinstance(authors_list, str):
            authors_list = [authors_list]
        authors = [str(a) for a in (authors_list or [])]

        forum_id = note.get("forum", note.get("id", ""))

        # Timestamps
        cdate = note.get("cdate") or note.get("tcdate")
        published_at = None
        if cdate:
            try:
                published_at = datetime.fromtimestamp(cdate / 1000)
            except (ValueError, TypeError, OSError):
                published_at = datetime(year, 1, 1)
        else:
            published_at = datetime(year, 1, 1)

        venue_short = venue_id.split(".")[0] if "." in venue_id else venue_id
        url = f"https://openreview.net/forum?id={forum_id}" if forum_id else ""

        canonical_key = (
            f"openreview:{forum_id}"
            if forum_id
            else f"hash:{hashlib.md5(title.encode()).hexdigest()[:16]}"
        )

        keywords_field = content.get("keywords", {})
        keywords = (
            keywords_field.get("value", [])
            if isinstance(keywords_field, dict)
            else keywords_field
        )
        if not isinstance(keywords, list):
            keywords = []

        # Extract review scores and decision if available
        decision_field = content.get("decision", {})
        decision = decision_field.get("value", "") if isinstance(decision_field, dict) else str(decision_field) if decision_field else ""
        tldr_field = content.get("TL;DR", content.get("TLDR", {}))
        tldr = tldr_field.get("value", "") if isinstance(tldr_field, dict) else str(tldr_field) if tldr_field else ""
        pdf_field = content.get("pdf", {})
        pdf_path = pdf_field.get("value", "") if isinstance(pdf_field, dict) else str(pdf_field) if pdf_field else ""
        pdf_url = f"https://openreview.net/pdf?id={forum_id}" if forum_id else ""

        return Paper(
            canonical_key=canonical_key,
            source_name="openreview",
            source_paper_id=forum_id,
            title=title,
            abstract=abstract,
            authors=authors,
            published_at=published_at,
            url=url,
            topics=[venue_short] + keywords[:5],
            venue=venue_short,
            pdf_url=pdf_url or None,
            metadata={
                "venue_id": venue_id,
                "forum_id": forum_id,
                "year": year,
                "decision": decision,
                "tldr": tldr,
                "keywords": keywords[:10],
                "pdf_url": pdf_url,
            },
        )
