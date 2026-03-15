"""Tests for source adapter parsing and download URL chain.

Verifies that papers produced by each adapter have the correct canonical_key,
source_paper_id, and metadata fields, so that _extract_arxiv_id and the
download URL fallback chain work correctly.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

import pytest

from paper_agent.domain.models.paper import Paper

_ARXIV_ID_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")


def _extract_arxiv_id(paper: Paper) -> str:
    """Mirror of the helper inside register_tools."""
    if paper.canonical_key.startswith("arxiv:"):
        return paper.canonical_key[6:]
    meta = paper.metadata or {}
    if meta.get("arxiv_id"):
        return meta["arxiv_id"]
    if _ARXIV_ID_RE.match(paper.source_paper_id or ""):
        return paper.source_paper_id
    return ""


def _build_pdf_url(paper: Paper) -> str | None:
    """Mirror the download URL chain from paper_download."""
    arxiv_id = _extract_arxiv_id(paper)
    meta = paper.metadata or {}
    if arxiv_id:
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    if meta.get("pdf_url"):
        return meta["pdf_url"]
    if meta.get("doi"):
        return f"https://doi.org/{meta['doi']}"
    return None


def _build_filename(paper: Paper) -> str:
    """Mirror the filename construction from paper_download."""
    arxiv_id = _extract_arxiv_id(paper)
    file_id = arxiv_id or paper.source_paper_id or paper.id
    file_id = re.sub(r"[/\\:]", "_", file_id)
    safe_name = re.sub(r"[^\w\s-]", "", paper.title)[:80].strip().replace(" ", "_")
    return f"{file_id}_{safe_name}.pdf"


# ── arXiv Adapter ────────────────────────────────────────────────────


class TestArxivAdapterParsing:
    def _parse(self) -> Paper:
        from paper_agent.infra.sources.arxiv_adapter import ArxivAdapter, ATOM_NS

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom"
              xmlns:arxiv="http://arxiv.org/schemas/atom">
          <entry>
            <id>http://arxiv.org/abs/2401.12345v1</id>
            <title>Attention Is All You Need</title>
            <summary>We propose transformers.</summary>
            <published>2024-01-15T00:00:00Z</published>
            <author><name>Alice</name></author>
            <author><name>Bob</name></author>
            <arxiv:primary_category term="cs.LG"/>
            <link href="http://arxiv.org/abs/2401.12345v1" type="text/html"/>
          </entry>
        </feed>"""

        adapter = ArxivAdapter()
        papers = adapter._parse_response(xml)
        assert len(papers) == 1
        return papers[0]

    def test_canonical_key(self):
        p = self._parse()
        assert p.canonical_key == "arxiv:2401.12345v1"

    def test_source_paper_id(self):
        p = self._parse()
        assert p.source_paper_id == "2401.12345v1"

    def test_extract_arxiv_id(self):
        p = self._parse()
        assert _extract_arxiv_id(p) == "2401.12345v1"

    def test_pdf_url(self):
        p = self._parse()
        url = _build_pdf_url(p)
        assert url == "https://arxiv.org/pdf/2401.12345v1.pdf"

    def test_filename_clean(self):
        p = self._parse()
        fn = _build_filename(p)
        assert "/" not in fn
        assert "2401.12345v1" in fn


# ── DBLP Adapter ─────────────────────────────────────────────────────


class TestDBLPAdapterParsing:
    def _parse(self) -> Paper:
        from paper_agent.infra.sources.dblp_adapter import DBLPAdapter

        hit_info = {
            "title": "DREAMPlace: Deep Learning Toolkit-Enabled GPU Acceleration.",
            "authors": {
                "author": [
                    {"@pid": "123/456", "text": "Yibo Lin"},
                    {"@pid": "789/012", "text": "David Z. Pan"},
                ]
            },
            "year": "2019",
            "ee": "https://doi.org/10.1145/3316781.3317803",
            "key": "conf/dac/LinSPWJP19",
            "venue": "DAC",
        }

        adapter = DBLPAdapter()
        paper = adapter._parse_hit(hit_info, "conf/dac")
        assert paper is not None
        return paper

    def test_canonical_key_is_dblp(self):
        p = self._parse()
        assert p.canonical_key.startswith("dblp:")
        assert "conf/dac" in p.canonical_key

    def test_source_paper_id_is_dblp_key(self):
        p = self._parse()
        assert p.source_paper_id == "conf/dac/LinSPWJP19"

    def test_extract_arxiv_id_returns_empty(self):
        """DBLP papers should NOT be mistaken for arXiv papers."""
        p = self._parse()
        assert _extract_arxiv_id(p) == ""

    def test_pdf_url_is_none(self):
        """DBLP papers without pdf_url or DOI in metadata should return None."""
        p = self._parse()
        url = _build_pdf_url(p)
        assert url is None

    def test_filename_no_slashes(self):
        """DBLP source_paper_id has slashes — filename must sanitize them."""
        p = self._parse()
        fn = _build_filename(p)
        assert "/" not in fn
        assert "\\" not in fn
        assert "conf_dac_LinSPWJP19" in fn


# ── Semantic Scholar Adapter ─────────────────────────────────────────


class TestS2AdapterParsing:
    def _parse(self, with_arxiv: bool = True) -> Paper:
        from paper_agent.infra.sources.semantic_scholar_adapter import (
            SemanticScholarAdapter,
        )

        hit: dict[str, Any] = {
            "paperId": "abc123def456",
            "title": "Graph Neural Network for Placement",
            "abstract": "We use GNN for placement.",
            "authors": [{"name": "Alice"}, {"name": "Bob"}],
            "year": 2024,
            "url": "https://www.semanticscholar.org/paper/abc123",
            "venue": "DAC",
            "externalIds": {
                "DOI": "10.1145/12345",
            },
            "citationCount": 42,
            "openAccessPdf": {"url": "https://example.com/paper.pdf"},
            "publicationVenue": {"name": "Design Automation Conference"},
            "publicationTypes": ["Conference"],
        }
        if with_arxiv:
            hit["externalIds"]["ArXiv"] = "2305.09876"

        adapter = SemanticScholarAdapter()
        paper = adapter._parse_hit(hit)
        assert paper is not None
        return paper

    def test_s2_with_arxiv_canonical_key(self):
        p = self._parse(with_arxiv=True)
        assert p.canonical_key == "arxiv:2305.09876"

    def test_s2_without_arxiv_canonical_key(self):
        p = self._parse(with_arxiv=False)
        assert p.canonical_key.startswith("doi:") or p.canonical_key.startswith("s2:")

    def test_source_paper_id_is_s2_id(self):
        """source_paper_id should always be the S2 hash, NOT the arXiv ID."""
        p = self._parse(with_arxiv=True)
        assert p.source_paper_id == "abc123def456"

    def test_extract_arxiv_id_with_arxiv(self):
        p = self._parse(with_arxiv=True)
        assert _extract_arxiv_id(p) == "2305.09876"

    def test_extract_arxiv_id_without_arxiv(self):
        p = self._parse(with_arxiv=False)
        assert _extract_arxiv_id(p) == ""

    def test_pdf_url_with_arxiv(self):
        p = self._parse(with_arxiv=True)
        url = _build_pdf_url(p)
        assert url == "https://arxiv.org/pdf/2305.09876.pdf"

    def test_pdf_url_without_arxiv_falls_back_to_open_access(self):
        p = self._parse(with_arxiv=False)
        url = _build_pdf_url(p)
        assert url == "https://example.com/paper.pdf"

    def test_pdf_url_no_open_access_falls_back_to_doi(self):
        from paper_agent.infra.sources.semantic_scholar_adapter import (
            SemanticScholarAdapter,
        )

        hit: dict[str, Any] = {
            "paperId": "xyz789",
            "title": "No PDF Paper",
            "abstract": "",
            "authors": [],
            "year": 2023,
            "url": "",
            "venue": "",
            "externalIds": {"DOI": "10.1145/99999"},
            "citationCount": 0,
            "openAccessPdf": None,
            "publicationVenue": None,
            "publicationTypes": [],
        }
        adapter = SemanticScholarAdapter()
        p = adapter._parse_hit(hit)
        assert p is not None
        url = _build_pdf_url(p)
        assert url == "https://doi.org/10.1145/99999"

    def test_filename_uses_arxiv_id_when_available(self):
        p = self._parse(with_arxiv=True)
        fn = _build_filename(p)
        assert "2305.09876" in fn
        assert "abc123def456" not in fn


# ── OpenReview Adapter ───────────────────────────────────────────────


class TestOpenReviewAdapterParsing:
    def _parse(self) -> Paper:
        from paper_agent.infra.sources.openreview_adapter import OpenReviewAdapter

        note = {
            "id": "note123",
            "forum": "forum456",
            "content": {
                "title": {"value": "Scaling Laws for Neural LMs"},
                "abstract": {"value": "We study scaling laws."},
                "authors": {"value": ["Alice", "Bob"]},
                "keywords": {"value": ["scaling", "LLM"]},
            },
            "cdate": 1704067200000,  # 2024-01-01 UTC
        }

        adapter = OpenReviewAdapter()
        paper = adapter._parse_note(note, "NeurIPS.cc", 2024)
        assert paper is not None
        return paper

    def test_canonical_key_is_openreview(self):
        p = self._parse()
        assert p.canonical_key == "openreview:forum456"

    def test_source_paper_id_is_forum_id(self):
        p = self._parse()
        assert p.source_paper_id == "forum456"

    def test_extract_arxiv_id_returns_empty(self):
        p = self._parse()
        assert _extract_arxiv_id(p) == ""

    def test_pdf_url_is_none(self):
        p = self._parse()
        url = _build_pdf_url(p)
        assert url is None

    def test_filename_clean(self):
        p = self._parse()
        fn = _build_filename(p)
        assert "/" not in fn
        assert "forum456" in fn


# ── ACL Anthology Adapter ───────────────────────────────────────────


class TestACLAnthologyAdapterParsing:
    def _parse(self) -> Paper:
        from paper_agent.infra.sources.acl_anthology_adapter import (
            ACLAnthologyAdapter,
        )

        xml = """<volume id="2024.acl-long">
          <paper id="42">
            <title>Code Generation with LLMs</title>
            <abstract>We propose a new method.</abstract>
            <author><first>Alice</first><last>Smith</last></author>
            <author><first>Bob</first><last>Jones</last></author>
            <url>2024.acl-long.42</url>
          </paper>
        </volume>"""

        adapter = ACLAnthologyAdapter()
        papers = adapter._parse_volume_xml(xml, "acl", 2024)
        assert len(papers) == 1
        return papers[0]

    def test_canonical_key_is_acl(self):
        p = self._parse()
        assert p.canonical_key.startswith("acl:")

    def test_source_paper_id(self):
        p = self._parse()
        assert p.source_paper_id == "42"

    def test_extract_arxiv_id_returns_empty(self):
        p = self._parse()
        assert _extract_arxiv_id(p) == ""

    def test_pdf_url_is_none(self):
        p = self._parse()
        url = _build_pdf_url(p)
        assert url is None

    def test_url_constructed(self):
        p = self._parse()
        assert "aclanthology.org" in p.url

    def test_filename_clean(self):
        p = self._parse()
        fn = _build_filename(p)
        assert "/" not in fn


# ── Cross-source download chain summary ──────────────────────────────


class TestDownloadChainAllSources:
    """Verify the full download chain doesn't produce 404-prone URLs."""

    @pytest.mark.parametrize(
        "canonical_key,source_paper_id,metadata,expected_has_url",
        [
            ("arxiv:2401.00001", "2401.00001", {}, True),
            ("dblp:conf/dac/Foo24", "conf/dac/Foo24", {}, False),
            ("s2:abc123", "abc123", {"arxiv_id": "2305.11111"}, True),
            ("s2:abc123", "abc123", {"pdf_url": "https://x.com/a.pdf"}, True),
            ("s2:abc123", "abc123", {"doi": "10.1145/999"}, True),
            ("s2:abc123", "abc123", {}, False),
            ("openreview:forum1", "forum1", {}, False),
            ("acl:2024.acl-long.42", "42", {}, False),
        ],
        ids=[
            "arxiv",
            "dblp-no-url",
            "s2-with-arxiv",
            "s2-with-pdf",
            "s2-with-doi",
            "s2-no-fallback",
            "openreview",
            "acl",
        ],
    )
    def test_url_or_skip(
        self,
        canonical_key: str,
        source_paper_id: str,
        metadata: dict,
        expected_has_url: bool,
    ):
        p = Paper(
            canonical_key=canonical_key,
            source_name="test",
            source_paper_id=source_paper_id,
            title="Test Paper",
            abstract="",
            authors=[],
            published_at=datetime(2024, 1, 1),
            url="",
            metadata=metadata,
        )
        url = _build_pdf_url(p)
        if expected_has_url:
            assert url is not None, f"Expected URL for {canonical_key}"
            assert "arxiv.org" in url or "doi.org" in url or "x.com" in url
        else:
            assert url is None, f"Expected no URL for {canonical_key}, got {url}"

    @pytest.mark.parametrize(
        "source_paper_id",
        [
            "conf/dac/LinSPWJP19",
            "conf/iccad/Test2024",
            "conf/date/Paper23",
        ],
    )
    def test_dblp_ids_never_in_arxiv_url(self, source_paper_id: str):
        """DBLP keys with slashes must never end up in arXiv PDF URLs."""
        p = Paper(
            canonical_key=f"dblp:{source_paper_id}",
            source_name="dblp",
            source_paper_id=source_paper_id,
            title="Test",
            abstract="",
            authors=[],
            published_at=datetime(2024, 1, 1),
            url="",
        )
        url = _build_pdf_url(p)
        assert url is None
        fn = _build_filename(p)
        assert "/" not in fn
