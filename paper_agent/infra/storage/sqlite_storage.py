"""SQLite-based local storage layer for Paper Agent."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any

from paper_agent.domain.models.paper import Paper
from paper_agent.domain.models.digest import Digest, DigestStats
from paper_agent.domain.models.collection import CollectionRecord

_SCHEMA_VERSION = 1

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,
    canonical_key TEXT UNIQUE,
    source_name TEXT NOT NULL,
    source_paper_id TEXT NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT NOT NULL DEFAULT '',
    authors_json TEXT NOT NULL DEFAULT '[]',
    published_at TEXT,
    url TEXT NOT NULL DEFAULT '',
    topics_json TEXT NOT NULL DEFAULT '[]',
    methodology_tags_json TEXT NOT NULL DEFAULT '[]',
    research_objectives_json TEXT NOT NULL DEFAULT '[]',
    relevance_score REAL NOT NULL DEFAULT 0.0,
    relevance_band TEXT NOT NULL DEFAULT '',
    recommendation_reason TEXT NOT NULL DEFAULT '',
    lifecycle_state TEXT NOT NULL DEFAULT 'discovered',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS collections (
    id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    trigger_type TEXT NOT NULL DEFAULT 'manual',
    status TEXT NOT NULL DEFAULT 'running',
    started_at TEXT NOT NULL,
    finished_at TEXT,
    collected_count INTEGER NOT NULL DEFAULT 0,
    new_count INTEGER NOT NULL DEFAULT 0,
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    error_summary_json TEXT
);

CREATE TABLE IF NOT EXISTS digests (
    id TEXT PRIMARY KEY,
    digest_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'generated',
    summary_json TEXT NOT NULL DEFAULT '{}',
    high_confidence_refs TEXT NOT NULL DEFAULT '[]',
    supplemental_refs TEXT NOT NULL DEFAULT '[]',
    artifact_uri TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS topic_reports (
    id TEXT PRIMARY KEY,
    topic_key TEXT NOT NULL,
    sections_json TEXT NOT NULL DEFAULT '[]',
    paper_refs TEXT NOT NULL DEFAULT '[]',
    artifact_uri TEXT,
    status TEXT NOT NULL DEFAULT 'generated',
    version_tag TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS surveys (
    id TEXT PRIMARY KEY,
    entry_point TEXT NOT NULL,
    entry_point_type TEXT NOT NULL DEFAULT 'topic',
    problem_definition TEXT NOT NULL DEFAULT '',
    method_taxonomy_json TEXT NOT NULL DEFAULT '[]',
    comparative_analysis_json TEXT,
    research_gaps_json TEXT NOT NULL DEFAULT '[]',
    future_directions_json TEXT NOT NULL DEFAULT '[]',
    sections_json TEXT NOT NULL DEFAULT '[]',
    paper_refs TEXT NOT NULL DEFAULT '[]',
    artifact_uri TEXT,
    status TEXT NOT NULL DEFAULT 'generated',
    version_tag TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS llm_cache (
    cache_key TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    task_type TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    response_json TEXT NOT NULL,
    prompt_version TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    expires_at TEXT
);

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE INDEX IF NOT EXISTS idx_papers_source_published
    ON papers(source_name, published_at);
CREATE INDEX IF NOT EXISTS idx_papers_relevance
    ON papers(relevance_score);
CREATE INDEX IF NOT EXISTS idx_papers_lifecycle
    ON papers(lifecycle_state);
CREATE INDEX IF NOT EXISTS idx_collections_source_started
    ON collections(source_name, started_at);
CREATE INDEX IF NOT EXISTS idx_digests_date
    ON digests(digest_date);
CREATE INDEX IF NOT EXISTS idx_topic_reports_topic
    ON topic_reports(topic_key, created_at);
CREATE INDEX IF NOT EXISTS idx_surveys_entry
    ON surveys(entry_point_type, created_at);
CREATE INDEX IF NOT EXISTS idx_llm_cache_provider
    ON llm_cache(provider, model, task_type);
"""

_FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
    title, abstract, topics_json, methodology_tags_json, research_objectives_json,
    content='papers',
    content_rowid='rowid'
);
"""

_FTS_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS papers_ai AFTER INSERT ON papers BEGIN
    INSERT INTO papers_fts(rowid, title, abstract, topics_json, methodology_tags_json, research_objectives_json)
    VALUES (new.rowid, new.title, new.abstract, new.topics_json, new.methodology_tags_json, new.research_objectives_json);
END;

CREATE TRIGGER IF NOT EXISTS papers_ad AFTER DELETE ON papers BEGIN
    INSERT INTO papers_fts(papers_fts, rowid, title, abstract, topics_json, methodology_tags_json, research_objectives_json)
    VALUES ('delete', old.rowid, old.title, old.abstract, old.topics_json, old.methodology_tags_json, old.research_objectives_json);
END;

CREATE TRIGGER IF NOT EXISTS papers_au AFTER UPDATE ON papers BEGIN
    INSERT INTO papers_fts(papers_fts, rowid, title, abstract, topics_json, methodology_tags_json, research_objectives_json)
    VALUES ('delete', old.rowid, old.title, old.abstract, old.topics_json, old.methodology_tags_json, old.research_objectives_json);
    INSERT INTO papers_fts(rowid, title, abstract, topics_json, methodology_tags_json, research_objectives_json)
    VALUES (new.rowid, new.title, new.abstract, new.topics_json, new.methodology_tags_json, new.research_objectives_json);
END;
"""


class SQLiteStorage:
    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def initialize(self) -> None:
        cur = self.conn.executescript(_SCHEMA_SQL)
        cur.close()
        self.conn.executescript(_FTS_SQL)
        self.conn.executescript(_FTS_TRIGGERS)
        existing = self.conn.execute("SELECT version FROM schema_version").fetchone()
        if not existing:
            self.conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)", (_SCHEMA_VERSION,)
            )
        self.conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── Papers ──

    def save_paper(self, paper: Paper) -> None:
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            """INSERT INTO papers
            (id, canonical_key, source_name, source_paper_id, title, abstract,
             authors_json, published_at, url, topics_json, methodology_tags_json,
             research_objectives_json, relevance_score, relevance_band,
             recommendation_reason, lifecycle_state, metadata_json, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(canonical_key) DO UPDATE SET
                relevance_score=excluded.relevance_score,
                relevance_band=excluded.relevance_band,
                recommendation_reason=excluded.recommendation_reason,
                topics_json=excluded.topics_json,
                methodology_tags_json=excluded.methodology_tags_json,
                research_objectives_json=excluded.research_objectives_json,
                lifecycle_state=excluded.lifecycle_state,
                updated_at=excluded.updated_at
            """,
            (
                paper.id,
                paper.canonical_key,
                paper.source_name,
                paper.source_paper_id,
                paper.title,
                paper.abstract,
                json.dumps(paper.authors),
                paper.published_at.isoformat() if paper.published_at else None,
                paper.url,
                json.dumps(paper.topics),
                json.dumps(paper.methodology_tags),
                json.dumps(paper.research_objectives),
                paper.relevance_score,
                paper.relevance_band,
                paper.recommendation_reason,
                paper.lifecycle_state,
                json.dumps(paper.metadata),
                now,
                now,
            ),
        )
        self.conn.commit()

    def save_papers(self, papers: list[Paper]) -> tuple[int, int]:
        new_count = 0
        dup_count = 0
        for p in papers:
            existing = self.conn.execute(
                "SELECT id FROM papers WHERE canonical_key = ?", (p.canonical_key,)
            ).fetchone()
            if existing:
                dup_count += 1
            else:
                new_count += 1
            self.save_paper(p)
        return new_count, dup_count

    def get_paper(self, paper_id: str) -> Paper | None:
        row = self.conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
        if not row:
            return None
        return self._row_to_paper(row)

    def get_paper_by_canonical(self, canonical_key: str) -> Paper | None:
        row = self.conn.execute(
            "SELECT * FROM papers WHERE canonical_key = ?", (canonical_key,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_paper(row)

    def get_papers_by_date(self, since: date, until: date | None = None) -> list[Paper]:
        if until:
            rows = self.conn.execute(
                "SELECT * FROM papers WHERE published_at >= ? AND published_at < ? ORDER BY relevance_score DESC",
                (since.isoformat(), until.isoformat()),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM papers WHERE published_at >= ? ORDER BY relevance_score DESC",
                (since.isoformat(),),
            ).fetchall()
        return [self._row_to_paper(r) for r in rows]

    def get_filtered_papers(self, min_score: float = 0.0, limit: int = 100) -> list[Paper]:
        rows = self.conn.execute(
            "SELECT * FROM papers WHERE relevance_score >= ? ORDER BY relevance_score DESC LIMIT ?",
            (min_score, limit),
        ).fetchall()
        return [self._row_to_paper(r) for r in rows]

    def search_papers(self, query: str, limit: int = 50) -> list[Paper]:
        rows = self.conn.execute(
            """SELECT p.* FROM papers_fts fts
               JOIN papers p ON p.rowid = fts.rowid
               WHERE papers_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (query, limit),
        ).fetchall()
        return [self._row_to_paper(r) for r in rows]

    def update_paper_scores(
        self, paper_id: str, score: float, band: str, reason: str,
        topics: list[str] | None = None,
    ) -> None:
        now = datetime.utcnow().isoformat()
        if topics is not None:
            self.conn.execute(
                """UPDATE papers SET relevance_score=?, relevance_band=?,
                   recommendation_reason=?, topics_json=?, lifecycle_state='filtered', updated_at=?
                   WHERE id=?""",
                (score, band, reason, json.dumps(topics), now, paper_id),
            )
        else:
            self.conn.execute(
                """UPDATE papers SET relevance_score=?, relevance_band=?,
                   recommendation_reason=?, lifecycle_state='filtered', updated_at=?
                   WHERE id=?""",
                (score, band, reason, now, paper_id),
            )
        self.conn.commit()

    def count_papers(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM papers").fetchone()
        return row["cnt"] if row else 0

    def get_all_papers(self, limit: int = 1000) -> list[Paper]:
        rows = self.conn.execute(
            "SELECT * FROM papers ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_paper(r) for r in rows]

    # ── Digests ──

    def save_digest(self, digest: Digest) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO digests
            (id, digest_date, status, summary_json, high_confidence_refs,
             supplemental_refs, artifact_uri, created_at)
            VALUES (?,?,?,?,?,?,?,?)""",
            (
                digest.id,
                digest.digest_date.isoformat(),
                digest.status,
                json.dumps(digest.stats.__dict__),
                json.dumps([p.id for p in digest.high_confidence_papers]),
                json.dumps([p.id for p in digest.supplemental_papers]),
                digest.artifact_uri,
                digest.created_at.isoformat(),
            ),
        )
        self.conn.commit()

    def get_latest_digest(self) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM digests ORDER BY digest_date DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        return dict(row)

    # ── Collections ──

    def save_collection(self, record: CollectionRecord) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO collections
            (id, source_name, trigger_type, status, started_at, finished_at,
             collected_count, new_count, duplicate_count, error_summary_json)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                record.id,
                record.source_name,
                record.trigger_type,
                record.status,
                record.started_at.isoformat(),
                record.finished_at.isoformat() if record.finished_at else None,
                record.collected_count,
                record.new_count,
                record.duplicate_count,
                json.dumps(record.error_summary) if record.error_summary else None,
            ),
        )
        self.conn.commit()

    # ── Internal ──

    def _row_to_paper(self, row: sqlite3.Row) -> Paper:
        pub = row["published_at"]
        return Paper(
            id=row["id"],
            canonical_key=row["canonical_key"],
            source_name=row["source_name"],
            source_paper_id=row["source_paper_id"],
            title=row["title"],
            abstract=row["abstract"],
            authors=json.loads(row["authors_json"]),
            published_at=datetime.fromisoformat(pub) if pub else None,
            url=row["url"],
            topics=json.loads(row["topics_json"]),
            methodology_tags=json.loads(row["methodology_tags_json"]),
            research_objectives=json.loads(row["research_objectives_json"]),
            relevance_score=row["relevance_score"],
            relevance_band=row["relevance_band"],
            recommendation_reason=row["recommendation_reason"],
            lifecycle_state=row["lifecycle_state"],
            metadata=json.loads(row["metadata_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
