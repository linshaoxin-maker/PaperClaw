"""arXiv paper collection adapter using the Atom API."""

from __future__ import annotations

import hashlib
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Any

import httpx

from paper_agent.domain.models.paper import Paper
from paper_agent.infra.sources.base_adapter import SourceAdapter

ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"

MAX_RESULTS_PER_REQUEST = 100
REQUEST_DELAY_SECONDS = 3.0


class ArxivAdapter(SourceAdapter):

    @property
    def api_type(self) -> str:
        return "arxiv"

    @property
    def rate_limit_delay(self) -> float:
        return REQUEST_DELAY_SECONDS

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._client = httpx.Client(timeout=30.0, follow_redirects=True, trust_env=True)

    # ── SourceAdapter interface ──

    def collect(
        self,
        api_config: dict,
        since: datetime | None = None,
        max_results: int = 200,
    ) -> list[Paper]:
        category = api_config.get("category", "")
        if not category:
            self._log("ArxivAdapter.collect: no category in api_config, skipping")
            return []
        return self._query_category(category, since, max_results=max_results)

    # ── Legacy convenience method (used by CLI/MCP online search) ──

    def collect_papers(
        self,
        categories: list[str],
        since: datetime | None = None,
        max_results: int = 200,
    ) -> list[Paper]:
        if since is None:
            since = datetime.utcnow() - timedelta(days=7)

        self._log(
            f"Starting arXiv collection: categories={categories}, "
            f"since={since.isoformat()}, max_results={max_results}"
        )

        all_papers: list[Paper] = []
        for cat in categories:
            self._progress(f"arXiv: 抓取分类 {cat} ...")
            self._log(f"Collecting category={cat}")
            papers = self._query_category(cat, since, max_results=max_results)
            self._progress(f"arXiv: {cat} 完成, {len(papers)} 篇")
            self._log(f"Finished category={cat}: collected={len(papers)}")
            all_papers.extend(papers)
            if len(categories) > 1:
                self._log(f"Sleeping {REQUEST_DELAY_SECONDS}s before next category")
                time.sleep(REQUEST_DELAY_SECONDS)
        self._log(f"Collection finished: total_collected={len(all_papers)}")
        return all_papers

    def get_paper_metadata(self, arxiv_id: str) -> Paper | None:
        query = f"id_list={arxiv_id}"
        url = f"{ARXIV_API_URL}?{query}"
        self._log(f"Fetching paper metadata: arxiv_id={arxiv_id}, url={url}")
        resp = self._client.get(url)
        self._log(f"Metadata response: status_code={resp.status_code}")
        if resp.status_code != 200:
            return None
        papers = self._parse_response(resp.text)
        return papers[0] if papers else None

    # ── Internal ──

    def _query_category(
        self, category: str, since: datetime | None, max_results: int
    ) -> list[Paper]:
        if since is None:
            since = datetime.utcnow() - timedelta(days=7)
        papers: list[Paper] = []
        start = 0
        while start < max_results:
            batch_size = min(MAX_RESULTS_PER_REQUEST, max_results - start)
            query = (
                f"search_query=cat:{category}&start={start}"
                f"&max_results={batch_size}&sortBy=submittedDate&sortOrder=descending"
            )
            url = f"{ARXIV_API_URL}?{query}"
            self._log(
                f"Requesting category={category}, start={start}, "
                f"batch_size={batch_size}, url={url}"
            )
            resp = self._client.get(url)
            self._log(
                f"Response category={category}, start={start}, "
                f"status_code={resp.status_code}"
            )
            if resp.status_code != 200:
                self._log(
                    f"Stopping category={category} due to non-200 response: "
                    f"status_code={resp.status_code}"
                )
                break

            batch = self._parse_response(resp.text)
            self._log(f"Parsed category={category}, start={start}: entries={len(batch)}")
            if not batch:
                self._log(f"Stopping category={category} because parsed batch is empty")
                break

            for p in batch:
                if p.published_at and p.published_at >= since:
                    papers.append(p)
                else:
                    self._log(
                        f"Stopping category={category} at "
                        f"paper={p.source_paper_id or p.title[:60]}: "
                        f"published_at="
                        f"{p.published_at.isoformat() if p.published_at else 'None'}, "
                        f"cutoff={since.isoformat()}"
                    )
                    return papers

            start += batch_size
            if len(batch) < batch_size:
                self._log(
                    f"Stopping category={category} because batch smaller than "
                    f"requested: {len(batch)} < {batch_size}"
                )
                break
            self._log(
                f"Sleeping {REQUEST_DELAY_SECONDS}s before next batch "
                f"for category={category}"
            )
            time.sleep(REQUEST_DELAY_SECONDS)

        return papers

    def _parse_response(self, xml_text: str) -> list[Paper]:
        papers: list[Paper] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            snippet = " ".join(xml_text.strip().split())[:200]
            self._log(f"XML parse failed: error={e}, response_snippet={snippet}")
            return papers

        for entry in root.findall(f"{ATOM_NS}entry"):
            paper = self._parse_entry(entry)
            if paper:
                papers.append(paper)
        return papers

    def _parse_entry(self, entry: ET.Element) -> Paper | None:
        title_el = entry.find(f"{ATOM_NS}title")
        if title_el is None or not title_el.text:
            return None

        title = " ".join(title_el.text.strip().split())
        abstract_el = entry.find(f"{ATOM_NS}summary")
        abstract = (
            " ".join(abstract_el.text.strip().split())
            if abstract_el is not None and abstract_el.text
            else ""
        )

        arxiv_id = ""
        id_el = entry.find(f"{ATOM_NS}id")
        if id_el is not None and id_el.text:
            arxiv_id = id_el.text.strip().split("/abs/")[-1]

        authors = []
        for author_el in entry.findall(f"{ATOM_NS}author"):
            name_el = author_el.find(f"{ATOM_NS}name")
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())

        published_at = None
        pub_el = entry.find(f"{ATOM_NS}published")
        if pub_el is not None and pub_el.text:
            try:
                published_at = datetime.fromisoformat(
                    pub_el.text.replace("Z", "+00:00")
                )
            except ValueError:
                pass

        categories = []
        for cat_el in entry.findall(f"{ARXIV_NS}primary_category"):
            term = cat_el.get("term", "")
            if term:
                categories.append(term)

        # Extract additional arXiv metadata
        pdf_url = ""
        for link_el in entry.findall(f"{ATOM_NS}link"):
            if link_el.get("title") == "pdf":
                pdf_url = link_el.get("href", "")
                break
        if not pdf_url and arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        # Updated date (arXiv papers can be revised)
        updated_at_str = ""
        upd_el = entry.find(f"{ATOM_NS}updated")
        if upd_el is not None and upd_el.text:
            updated_at_str = upd_el.text.strip()

        # Comment field (often contains page count, conference info)
        comment = ""
        comment_el = entry.find(f"{ARXIV_NS}comment")
        if comment_el is not None and comment_el.text:
            comment = comment_el.text.strip()

        # Journal reference
        journal_ref = ""
        jref_el = entry.find(f"{ARXIV_NS}journal_ref")
        if jref_el is not None and jref_el.text:
            journal_ref = jref_el.text.strip()

        # DOI
        doi = ""
        doi_el = entry.find(f"{ARXIV_NS}doi")
        if doi_el is not None and doi_el.text:
            doi = doi_el.text.strip()

        # All categories (primary + secondary)
        all_categories = list(categories)
        for cat_el in entry.findall(f"{ATOM_NS}category"):
            term = cat_el.get("term", "")
            if term and term not in all_categories:
                all_categories.append(term)

        canonical_key = (
            f"arxiv:{arxiv_id}"
            if arxiv_id
            else f"hash:{hashlib.md5(title.encode()).hexdigest()[:16]}"
        )

        # Derive venue from journal_ref or comment
        venue = ""
        if journal_ref:
            venue = journal_ref
        elif comment:
            # Try to extract conference name from comment (e.g. "Accepted at NeurIPS 2024")
            import re
            conf_match = re.search(r'(?:accepted|published|appear)\s+(?:at|in|by)\s+(\w[\w\s&-]+)', comment, re.IGNORECASE)
            if conf_match:
                venue = conf_match.group(1).strip()

        return Paper(
            canonical_key=canonical_key,
            source_name="arxiv",
            source_paper_id=arxiv_id,
            title=title,
            abstract=abstract,
            authors=authors,
            published_at=published_at,
            url=url,
            topics=categories,
            doi=doi or None,
            venue=venue,
            pdf_url=pdf_url or None,
            metadata={
                "arxiv_categories": all_categories,
                "comment": comment,
                "journal_ref": journal_ref,
                "doi": doi,
                "pdf_url": pdf_url,
                "updated_at": updated_at_str,
            },
        )
