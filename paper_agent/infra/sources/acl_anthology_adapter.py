"""ACL Anthology paper collection adapter.

Fetches papers from ACL-hosted conferences (ACL, EMNLP, NAACL, COLING)
via the ACL Anthology API.

The Anthology provides a REST endpoint that returns structured JSON for
proceedings and volumes.
"""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

import httpx

from paper_agent.domain.models.paper import Paper
from paper_agent.infra.sources.base_adapter import SourceAdapter

ANTHOLOGY_API_URL = "https://aclanthology.org"


class ACLAnthologyAdapter(SourceAdapter):

    @property
    def api_type(self) -> str:
        return "acl_anthology"

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
            self._log("ACLAnthologyAdapter: no venue_key, skipping")
            return []

        since_year = since.year if since else datetime.utcnow().year
        return self._query_venue(venue_key, since_year, max_results)

    def _query_venue(
        self, venue_key: str, since_year: int, max_results: int
    ) -> list[Paper]:
        all_papers: list[Paper] = []
        current_year = datetime.utcnow().year

        for year in range(current_year, since_year - 1, -1):
            if len(all_papers) >= max_results:
                break
            papers = self._fetch_year(venue_key, year, max_results - len(all_papers))
            all_papers.extend(papers)

        self._log(f"ACL Anthology: collected {len(all_papers)} from {venue_key}")
        return all_papers

    def _fetch_year(
        self, venue_key: str, year: int, max_results: int
    ) -> list[Paper]:
        """Fetch papers for a given venue and year from ACL Anthology."""
        # ACL Anthology exposes event pages as structured HTML/XML
        # Try the JSON endpoint first (newer API)
        papers = self._try_json_api(venue_key, year, max_results)
        if papers:
            return papers

        # Fallback: scrape the MODS/BibTeX XML export
        return self._try_xml_export(venue_key, year, max_results)

    def _try_json_api(
        self, venue_key: str, year: int, max_results: int
    ) -> list[Paper]:
        """Try the ACL Anthology JSON API endpoint."""
        url = f"{ANTHOLOGY_API_URL}/events/{venue_key}-{year}"
        self._log(f"ACL Anthology JSON: url={url}")

        try:
            resp = self._client.get(url, headers={"Accept": "application/json"})
        except httpx.HTTPError as e:
            self._log(f"ACL Anthology HTTP error: {e}")
            return []

        if resp.status_code != 200:
            self._log(f"ACL Anthology non-200: {resp.status_code}")
            return []

        # The event page returns HTML; parse paper links from it
        return self._parse_event_page(resp.text, venue_key, year, max_results)

    def _parse_event_page(
        self, html: str, venue_key: str, year: int, max_results: int
    ) -> list[Paper]:
        """Extract paper info from ACL Anthology event page HTML.

        This is a best-effort parser — ACL Anthology pages have a consistent
        structure with <span class="d-block"> for titles and author lists.
        """
        papers: list[Paper] = []
        # Look for paper IDs in the HTML (format: {year}.{venue}-{section}.{number})
        import re

        # Match anthology IDs like "2025.acl-long.1"
        pattern = rf"({year}\.{venue_key}[\w-]*\.\d+)"
        ids_found = list(dict.fromkeys(re.findall(pattern, html)))

        for anthology_id in ids_found[:max_results]:
            paper = self._fetch_single_paper(anthology_id, venue_key, year)
            if paper:
                papers.append(paper)
                if len(papers) >= max_results:
                    break

        return papers

    def _fetch_single_paper(
        self, anthology_id: str, venue_key: str, year: int
    ) -> Paper | None:
        """Fetch metadata for a single paper via BibTeX export."""
        url = f"{ANTHOLOGY_API_URL}/{anthology_id}.xml"
        self._log(f"ACL single paper: {url}")

        try:
            resp = self._client.get(url)
        except httpx.HTTPError:
            return None
        if resp.status_code != 200:
            return None

        return self._parse_mods_xml(resp.text, anthology_id, venue_key, year)

    def _try_xml_export(
        self, venue_key: str, year: int, max_results: int
    ) -> list[Paper]:
        """Try fetching volume XML from ACL Anthology."""
        # Common volume patterns
        volume_patterns = [
            f"{year}.{venue_key}-long",
            f"{year}.{venue_key}-short",
            f"{year}.{venue_key}-main",
            f"{year}.{venue_key}",
        ]

        papers: list[Paper] = []
        for vol_id in volume_patterns:
            if len(papers) >= max_results:
                break
            url = f"{ANTHOLOGY_API_URL}/{vol_id}.xml"
            self._log(f"ACL XML export: url={url}")

            try:
                resp = self._client.get(url)
            except httpx.HTTPError:
                continue
            if resp.status_code != 200:
                continue

            batch = self._parse_volume_xml(resp.text, venue_key, year)
            papers.extend(batch[: max_results - len(papers)])

        return papers

    def _parse_volume_xml(
        self, xml_text: str, venue_key: str, year: int
    ) -> list[Paper]:
        papers: list[Paper] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            self._log(f"ACL XML parse error: {e}")
            return papers

        for paper_el in root.iter("paper"):
            paper = self._xml_element_to_paper(paper_el, venue_key, year)
            if paper:
                papers.append(paper)

        return papers

    def _parse_mods_xml(
        self, xml_text: str, anthology_id: str, venue_key: str, year: int
    ) -> Paper | None:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return None

        for paper_el in root.iter("paper"):
            return self._xml_element_to_paper(
                paper_el, venue_key, year, override_id=anthology_id
            )
        return None

    def _xml_element_to_paper(
        self,
        el: ET.Element,
        venue_key: str,
        year: int,
        override_id: str = "",
    ) -> Paper | None:
        title_el = el.find("title")
        if title_el is None or not title_el.text:
            return None

        title = " ".join((title_el.text or "").strip().split())
        if not title:
            return None

        abstract_el = el.find("abstract")
        abstract = ""
        if abstract_el is not None and abstract_el.text:
            abstract = " ".join(abstract_el.text.strip().split())

        authors: list[str] = []
        for author_el in el.findall("author"):
            first = (author_el.findtext("first") or "").strip()
            last = (author_el.findtext("last") or "").strip()
            name = f"{first} {last}".strip()
            if name:
                authors.append(name)

        anthology_id = override_id or el.get("id", "")
        url_el = el.find("url")
        url = ""
        if url_el is not None and url_el.text:
            raw_url = url_el.text.strip()
            url = (
                raw_url
                if raw_url.startswith("http")
                else f"{ANTHOLOGY_API_URL}/{raw_url}"
            )
        elif anthology_id:
            url = f"{ANTHOLOGY_API_URL}/{anthology_id}"

        published_at = datetime(year, 1, 1)

        canonical_key = (
            f"acl:{anthology_id}"
            if anthology_id
            else f"hash:{hashlib.md5(title.encode()).hexdigest()[:16]}"
        )

        venue_short = venue_key.upper()

        return Paper(
            canonical_key=canonical_key,
            source_name="acl_anthology",
            source_paper_id=anthology_id,
            title=title,
            abstract=abstract,
            authors=authors,
            published_at=published_at,
            url=url,
            topics=[venue_short],
            metadata={
                "anthology_id": anthology_id,
                "venue_key": venue_key,
                "year": year,
            },
        )
