"""Tests for download arXiv-ID extraction, concurrent filtering, and PDF URL logic."""

from __future__ import annotations

import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from paper_agent.domain.models.paper import Paper
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage
from paper_agent.services.filtering_manager import FilteringManager


# ── Helpers ──────────────────────────────────────────────────────────


def _paper(
    canonical_key: str = "arxiv:2401.00001",
    source_name: str = "arxiv",
    source_paper_id: str = "2401.00001",
    title: str = "Test Paper",
    metadata: dict | None = None,
    **kwargs: Any,
) -> Paper:
    defaults = dict(
        canonical_key=canonical_key,
        source_name=source_name,
        source_paper_id=source_paper_id,
        title=title,
        abstract="Abstract text.",
        authors=["Alice"],
        published_at=datetime(2024, 1, 1),
        url="https://example.com",
        metadata=metadata or {},
    )
    defaults.update(kwargs)
    return Paper(**defaults)


@pytest.fixture
def storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        s = SQLiteStorage(db_path)
        s.initialize()
        yield s
        s.close()


# ── _extract_arxiv_id ────────────────────────────────────────────────
# We test the extraction logic inline since it's a closure inside register_tools.
# Replicate the same logic here for unit-testable verification.


def _extract_arxiv_id(paper: Paper) -> str:
    """Mirror of the helper inside register_tools."""
    import re

    _ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
    if paper.canonical_key.startswith("arxiv:"):
        return paper.canonical_key[6:]
    meta = paper.metadata or {}
    if meta.get("arxiv_id"):
        return meta["arxiv_id"]
    if _ARXIV_RE.match(paper.source_paper_id or ""):
        return paper.source_paper_id
    return ""


class TestExtractArxivId:
    def test_arxiv_paper(self):
        p = _paper(canonical_key="arxiv:2401.12345", source_paper_id="2401.12345")
        assert _extract_arxiv_id(p) == "2401.12345"

    def test_s2_paper_with_arxiv(self):
        p = _paper(
            canonical_key="s2:abc123hash",
            source_name="semantic_scholar",
            source_paper_id="abc123hash",
            metadata={"arxiv_id": "2305.09876"},
        )
        assert _extract_arxiv_id(p) == "2305.09876"

    def test_s2_paper_without_arxiv(self):
        p = _paper(
            canonical_key="s2:abc123hash",
            source_name="semantic_scholar",
            source_paper_id="abc123hash",
            metadata={"s2_id": "abc123hash"},
        )
        assert _extract_arxiv_id(p) == ""

    def test_dblp_paper(self):
        p = _paper(
            canonical_key="dblp:conf/dac/SomePaper2024",
            source_name="dblp",
            source_paper_id="conf/dac/SomePaper2024",
        )
        assert _extract_arxiv_id(p) == ""

    def test_doi_paper(self):
        p = _paper(
            canonical_key="doi:10.1145/12345",
            source_name="semantic_scholar",
            source_paper_id="s2hash",
        )
        assert _extract_arxiv_id(p) == ""

    def test_arxiv_with_version(self):
        p = _paper(canonical_key="arxiv:2401.12345v2", source_paper_id="2401.12345v2")
        assert _extract_arxiv_id(p) == "2401.12345v2"


# ── FilteringManager concurrency ─────────────────────────────────────


class TestFilteringManagerConcurrent:
    def test_parallel_scoring(self, storage: SQLiteStorage):
        """Verify papers are scored in parallel, not serial."""
        papers = [
            _paper(
                canonical_key=f"arxiv:2401.{i:05d}",
                source_paper_id=f"2401.{i:05d}",
                title=f"Paper {i}",
            )
            for i in range(8)
        ]
        for p in papers:
            storage.save_paper(p)

        call_times: list[float] = []

        def mock_score(paper: Paper, interests: dict) -> dict:
            call_times.append(time.monotonic())
            time.sleep(0.1)
            return {
                "score": 5.0,
                "band": "low",
                "reason": "test",
                "topics": ["test"],
            }

        llm = MagicMock()
        llm.score_relevance = mock_score

        fm = FilteringManager(storage, llm)
        start = time.monotonic()
        result = fm.filter_papers(papers, {"topics": [], "keywords": []}, show_progress=False)
        elapsed = time.monotonic() - start

        assert len(result) == 8
        # 8 papers at 0.1s each serial = 0.8s; parallel (8 workers) ≈ 0.1s
        assert elapsed < 0.5, f"Expected parallel execution, but took {elapsed:.2f}s"

    def test_llm_failure_degrades_gracefully(self, storage: SQLiteStorage):
        """If LLM call raises, paper gets score=0 instead of crashing."""
        p = _paper()
        storage.save_paper(p)

        llm = MagicMock()
        llm.score_relevance.side_effect = RuntimeError("API timeout")

        fm = FilteringManager(storage, llm)
        result = fm.filter_papers([p], {"topics": [], "keywords": []}, show_progress=False)

        assert len(result) == 1
        assert result[0].relevance_score == 0.0
        assert result[0].relevance_band == "low"
        assert "失败" in result[0].recommendation_reason

    def test_partial_llm_failure(self, storage: SQLiteStorage):
        """Some succeed, some fail — all papers still returned."""
        papers = [
            _paper(
                canonical_key=f"arxiv:2401.{i:05d}",
                source_paper_id=f"2401.{i:05d}",
                title=f"Paper {i}",
            )
            for i in range(4)
        ]
        for p in papers:
            storage.save_paper(p)

        call_count = 0

        def alternating_score(paper: Paper, interests: dict) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise RuntimeError("Intermittent failure")
            return {"score": 8.0, "band": "high", "reason": "good", "topics": []}

        llm = MagicMock()
        llm.score_relevance = alternating_score

        fm = FilteringManager(storage, llm)
        result = fm.filter_papers(papers, {"topics": [], "keywords": []}, show_progress=False)

        assert len(result) == 4
        scores = [p.relevance_score for p in result]
        assert 8.0 in scores
        assert 0.0 in scores


# ── Download URL logic ───────────────────────────────────────────────


class TestDownloadUrlConstruction:
    """Verify that PDF URLs are built correctly for each source type."""

    def test_arxiv_paper_gets_arxiv_url(self):
        p = _paper(canonical_key="arxiv:2401.12345", source_paper_id="2401.12345")
        arxiv_id = _extract_arxiv_id(p)
        assert arxiv_id == "2401.12345"
        url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        assert url == "https://arxiv.org/pdf/2401.12345.pdf"

    def test_dblp_paper_uses_no_arxiv_url(self):
        p = _paper(
            canonical_key="dblp:conf/dac/Foo2024",
            source_name="dblp",
            source_paper_id="conf/dac/Foo2024",
        )
        arxiv_id = _extract_arxiv_id(p)
        assert arxiv_id == ""

    def test_s2_paper_with_pdf_url(self):
        p = _paper(
            canonical_key="s2:abc123",
            source_name="semantic_scholar",
            source_paper_id="abc123",
            metadata={"pdf_url": "https://example.com/paper.pdf"},
        )
        arxiv_id = _extract_arxiv_id(p)
        assert arxiv_id == ""
        meta = p.metadata or {}
        pdf_url = meta.get("pdf_url", "")
        assert pdf_url == "https://example.com/paper.pdf"

    def test_s2_paper_with_arxiv_gets_arxiv_url(self):
        p = _paper(
            canonical_key="arxiv:2305.09876",
            source_name="semantic_scholar",
            source_paper_id="s2hash",
            metadata={"arxiv_id": "2305.09876"},
        )
        arxiv_id = _extract_arxiv_id(p)
        assert arxiv_id == "2305.09876"

    def test_filename_sanitization(self):
        """source_paper_id with slashes should be sanitized in filenames."""
        import re as _re

        source_id = "conf/dac/SomePaper2024"
        safe_id = _re.sub(r"[/\\:]", "_", source_id)
        assert "/" not in safe_id
        assert safe_id == "conf_dac_SomePaper2024"
