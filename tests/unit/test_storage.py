"""Unit tests for SQLite storage layer."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from paper_agent.domain.models.paper import Paper
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage


@pytest.fixture
def storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        s = SQLiteStorage(db_path)
        s.initialize()
        yield s
        s.close()


def _make_paper(**kwargs) -> Paper:
    defaults = dict(
        canonical_key="arxiv:2401.00001",
        source_name="arxiv",
        source_paper_id="2401.00001",
        title="Test Paper on Retrieval Augmented Generation",
        abstract="We propose a novel approach to RAG that improves retrieval planning.",
        authors=["Alice", "Bob"],
        published_at=datetime(2024, 1, 15),
        url="https://arxiv.org/abs/2401.00001",
        topics=["cs.AI", "RAG"],
    )
    defaults.update(kwargs)
    return Paper(**defaults)


class TestSQLiteStorage:
    def test_save_and_get_paper(self, storage: SQLiteStorage):
        paper = _make_paper()
        storage.save_paper(paper)
        loaded = storage.get_paper(paper.id)
        assert loaded is not None
        assert loaded.title == paper.title
        assert loaded.authors == ["Alice", "Bob"]

    def test_save_papers_dedup(self, storage: SQLiteStorage):
        p1 = _make_paper()
        p2 = _make_paper(id="other_id")
        new, dup = storage.save_papers([p1, p2])
        assert new == 1
        assert dup == 1

    def test_search_fts(self, storage: SQLiteStorage):
        paper = _make_paper()
        storage.save_paper(paper)
        results = storage.search_papers("retrieval augmented")
        assert len(results) >= 1
        assert results[0].title == paper.title

    def test_count(self, storage: SQLiteStorage):
        assert storage.count_papers() == 0
        storage.save_paper(_make_paper())
        assert storage.count_papers() == 1

    def test_update_scores(self, storage: SQLiteStorage):
        paper = _make_paper()
        storage.save_paper(paper)
        storage.update_paper_scores(paper.id, 8.5, "high", "Very relevant", ["RAG", "planning"])
        loaded = storage.get_paper(paper.id)
        assert loaded is not None
        assert loaded.relevance_score == 8.5
        assert loaded.relevance_band == "high"
        assert "RAG" in loaded.topics

    def test_get_by_canonical(self, storage: SQLiteStorage):
        paper = _make_paper()
        storage.save_paper(paper)
        loaded = storage.get_paper_by_canonical("arxiv:2401.00001")
        assert loaded is not None
        assert loaded.id == paper.id
