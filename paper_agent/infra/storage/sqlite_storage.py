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

_SCHEMA_VERSION = 4

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
    reading_status TEXT DEFAULT NULL,
    reading_status_at TEXT DEFAULT NULL,
    citation_count INTEGER DEFAULT NULL,
    doi TEXT DEFAULT NULL,
    venue TEXT NOT NULL DEFAULT '',
    pdf_url TEXT DEFAULT NULL,
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
CREATE TABLE IF NOT EXISTS paper_notes (
    id TEXT PRIMARY KEY,
    paper_id TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);
CREATE INDEX IF NOT EXISTS idx_paper_notes_paper ON paper_notes(paper_id);

CREATE TABLE IF NOT EXISTS paper_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_group_items (
    group_id TEXT NOT NULL,
    paper_id TEXT NOT NULL,
    added_at TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (group_id, paper_id),
    FOREIGN KEY (group_id) REFERENCES paper_groups(id),
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);

CREATE INDEX IF NOT EXISTS idx_llm_cache_provider
    ON llm_cache(provider, model, task_type);
"""

_V2_MIGRATION_SQL = """
-- v02: reading status on papers
ALTER TABLE papers ADD COLUMN reading_status TEXT DEFAULT NULL;
ALTER TABLE papers ADD COLUMN reading_status_at TEXT DEFAULT NULL;

-- v02: paper notes
CREATE TABLE IF NOT EXISTS paper_notes (
    id TEXT PRIMARY KEY,
    paper_id TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);
CREATE INDEX IF NOT EXISTS idx_paper_notes_paper ON paper_notes(paper_id);

-- v02: paper groups (user collections, distinct from 'collections' run-log table)
CREATE TABLE IF NOT EXISTS paper_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS paper_group_items (
    group_id TEXT NOT NULL,
    paper_id TEXT NOT NULL,
    added_at TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (group_id, paper_id),
    FOREIGN KEY (group_id) REFERENCES paper_groups(id),
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);
"""

_V3_MIGRATION_SQL = """
-- v03: paper contents (PDF full-text parsing)
CREATE TABLE IF NOT EXISTS paper_contents (
    paper_id TEXT PRIMARY KEY,
    sections_json TEXT NOT NULL DEFAULT '[]',
    tables_json TEXT NOT NULL DEFAULT '[]',
    figure_captions_json TEXT NOT NULL DEFAULT '[]',
    raw_text TEXT NOT NULL DEFAULT '',
    parsed_at TEXT NOT NULL,
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);

-- v03: paper profiles (structured extraction)
CREATE TABLE IF NOT EXISTS paper_profiles (
    paper_id TEXT PRIMARY KEY,
    task TEXT NOT NULL DEFAULT '',
    method_family TEXT NOT NULL DEFAULT '',
    method_name TEXT NOT NULL DEFAULT '',
    datasets_json TEXT NOT NULL DEFAULT '[]',
    baselines_json TEXT NOT NULL DEFAULT '[]',
    metrics_json TEXT NOT NULL DEFAULT '[]',
    best_results_json TEXT NOT NULL DEFAULT '{}',
    code_url TEXT,
    venue TEXT NOT NULL DEFAULT '',
    compute_cost TEXT,
    limitations_json TEXT NOT NULL DEFAULT '[]',
    extracted_from TEXT NOT NULL DEFAULT 'abstract',
    extracted_at TEXT NOT NULL,
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);
CREATE INDEX IF NOT EXISTS idx_profiles_task ON paper_profiles(task);
CREATE INDEX IF NOT EXISTS idx_profiles_method ON paper_profiles(method_family);

-- v03: user feedback
CREATE TABLE IF NOT EXISTS user_feedback (
    id TEXT PRIMARY KEY,
    paper_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL,
    value TEXT NOT NULL,
    context TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);
CREATE INDEX IF NOT EXISTS idx_feedback_paper ON user_feedback(paper_id);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON user_feedback(feedback_type);

-- v03: watchlist
CREATE TABLE IF NOT EXISTS watchlist (
    id TEXT PRIMARY KEY,
    watch_type TEXT NOT NULL,
    watch_value TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    last_checked TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_watchlist_type ON watchlist(watch_type);

-- v03: credibility assessments
CREATE TABLE IF NOT EXISTS credibility_assessments (
    paper_id TEXT PRIMARY KEY,
    code_available INTEGER,
    code_url TEXT,
    open_data INTEGER,
    venue_tier TEXT NOT NULL DEFAULT 'unknown',
    citation_count INTEGER,
    citation_velocity REAL,
    claim_aggressiveness TEXT NOT NULL DEFAULT 'unknown',
    baseline_completeness TEXT NOT NULL DEFAULT 'unknown',
    reproducibility_risk TEXT NOT NULL DEFAULT 'unknown',
    overall_confidence TEXT NOT NULL DEFAULT 'unknown',
    assessment_notes TEXT NOT NULL DEFAULT '',
    assessed_at TEXT NOT NULL,
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);

-- v03: research context
CREATE TABLE IF NOT EXISTS research_context (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    current_project TEXT NOT NULL DEFAULT '',
    current_baseline TEXT NOT NULL DEFAULT '',
    current_questions_json TEXT NOT NULL DEFAULT '[]',
    active_reading_group TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);
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


import re

_FTS_SPECIAL = re.compile(r'[:\-\.\(\)\*\^~"\{\}]')


def _sanitize_fts_query(query: str) -> str:
    """Make a user query safe for FTS5 MATCH.

    FTS5 treats hyphens as column-prefix operators (``long-term`` becomes
    ``long:term``) and other punctuation as syntax.  We quote any token
    that contains special characters so FTS5 treats it as a literal.
    """
    tokens = query.split()
    safe: list[str] = []
    for t in tokens:
        if _FTS_SPECIAL.search(t):
            # Strip existing quotes, then wrap in double quotes
            cleaned = t.replace('"', "")
            if cleaned:
                safe.append(f'"{cleaned}"')
        else:
            safe.append(t)
    return " ".join(safe) if safe else query


_V4_MIGRATION_SQL = """
-- v04: promote high-frequency metadata fields to first-class columns
ALTER TABLE papers ADD COLUMN citation_count INTEGER DEFAULT NULL;
ALTER TABLE papers ADD COLUMN doi TEXT DEFAULT NULL;
ALTER TABLE papers ADD COLUMN venue TEXT NOT NULL DEFAULT '';
ALTER TABLE papers ADD COLUMN pdf_url TEXT DEFAULT NULL;
"""


def _quote_all_tokens(query: str) -> str:
    """Last-resort fallback: quote every token individually."""
    tokens = query.split()
    return " ".join(f'"{t.replace(chr(34), "")}"' for t in tokens if t.strip())


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
            self._migrate_to_v3()
            self._migrate_to_v4()
            self.conn.commit()
        else:
            current = existing["version"]
            if current < 2:
                self._migrate_to_v2()
            if current < 3:
                self._migrate_to_v3()
            if current < 4:
                self._migrate_to_v4()
            self.conn.commit()

    def _migrate_to_v2(self) -> None:
        cols = {
            row[1]
            for row in self.conn.execute("PRAGMA table_info(papers)").fetchall()
        }
        if "reading_status" not in cols:
            self.conn.execute(
                "ALTER TABLE papers ADD COLUMN reading_status TEXT DEFAULT NULL"
            )
            self.conn.execute(
                "ALTER TABLE papers ADD COLUMN reading_status_at TEXT DEFAULT NULL"
            )
        for stmt in (
            """CREATE TABLE IF NOT EXISTS paper_notes (
                id TEXT PRIMARY KEY, paper_id TEXT NOT NULL,
                content TEXT NOT NULL, source TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                FOREIGN KEY (paper_id) REFERENCES papers(id))""",
            "CREATE INDEX IF NOT EXISTS idx_paper_notes_paper ON paper_notes(paper_id)",
            """CREATE TABLE IF NOT EXISTS paper_groups (
                id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""",
            """CREATE TABLE IF NOT EXISTS paper_group_items (
                group_id TEXT NOT NULL, paper_id TEXT NOT NULL,
                added_at TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (group_id, paper_id),
                FOREIGN KEY (group_id) REFERENCES paper_groups(id),
                FOREIGN KEY (paper_id) REFERENCES papers(id))""",
        ):
            self.conn.execute(stmt)
        self.conn.execute(
            "UPDATE schema_version SET version = ?", (_SCHEMA_VERSION,)
        )

    def _migrate_to_v3(self) -> None:
        for stmt in _V3_MIGRATION_SQL.strip().split(";"):
            # Strip leading/trailing whitespace and comment-only lines
            lines = [ln for ln in stmt.strip().splitlines() if ln.strip() and not ln.strip().startswith("--")]
            cleaned = "\n".join(lines).strip()
            if cleaned:
                try:
                    self.conn.execute(cleaned)
                except sqlite3.OperationalError:
                    pass
        self.conn.execute(
            "UPDATE schema_version SET version = ?", (_SCHEMA_VERSION,)
        )

    def _migrate_to_v4(self) -> None:
        cols = {
            row[1]
            for row in self.conn.execute("PRAGMA table_info(papers)").fetchall()
        }
        new_cols = {
            "citation_count": "INTEGER DEFAULT NULL",
            "doi": "TEXT DEFAULT NULL",
            "venue": "TEXT NOT NULL DEFAULT ''",
            "pdf_url": "TEXT DEFAULT NULL",
        }
        for col_name, col_def in new_cols.items():
            if col_name not in cols:
                try:
                    self.conn.execute(f"ALTER TABLE papers ADD COLUMN {col_name} {col_def}")
                except sqlite3.OperationalError:
                    pass
        # Backfill from metadata_json for existing papers
        rows = self.conn.execute(
            "SELECT id, metadata_json FROM papers WHERE metadata_json != '{}'"
        ).fetchall()
        for row in rows:
            try:
                meta = json.loads(row["metadata_json"])
                updates = {}
                if meta.get("citation_count") or meta.get("citationCount"):
                    updates["citation_count"] = meta.get("citation_count") or meta.get("citationCount")
                if meta.get("doi"):
                    updates["doi"] = meta["doi"]
                if meta.get("venue"):
                    updates["venue"] = meta["venue"]
                if meta.get("pdf_url"):
                    updates["pdf_url"] = meta["pdf_url"]
                if updates:
                    set_clause = ", ".join(f"{k} = ?" for k in updates)
                    self.conn.execute(
                        f"UPDATE papers SET {set_clause} WHERE id = ?",
                        [*updates.values(), row["id"]],
                    )
            except (json.JSONDecodeError, TypeError):
                pass
        self.conn.execute(
            "UPDATE schema_version SET version = ?", (_SCHEMA_VERSION,)
        )
        # Also add new columns to paper_profiles if they exist
        try:
            profile_cols = {
                row[1]
                for row in self.conn.execute("PRAGMA table_info(paper_profiles)").fetchall()
            }
            profile_new_cols = {
                "novelty_claim": "TEXT NOT NULL DEFAULT ''",
                "problem_formulation": "TEXT NOT NULL DEFAULT ''",
                "key_contributions_json": "TEXT NOT NULL DEFAULT '[]'",
            }
            for col_name, col_def in profile_new_cols.items():
                if col_name not in profile_cols:
                    try:
                        self.conn.execute(f"ALTER TABLE paper_profiles ADD COLUMN {col_name} {col_def}")
                    except sqlite3.OperationalError:
                        pass
        except sqlite3.OperationalError:
            pass  # paper_profiles table may not exist yet

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
             recommendation_reason, lifecycle_state, metadata_json,
             citation_count, doi, venue, pdf_url,
             created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(canonical_key) DO UPDATE SET
                relevance_score=excluded.relevance_score,
                relevance_band=excluded.relevance_band,
                recommendation_reason=excluded.recommendation_reason,
                topics_json=excluded.topics_json,
                methodology_tags_json=excluded.methodology_tags_json,
                research_objectives_json=excluded.research_objectives_json,
                lifecycle_state=excluded.lifecycle_state,
                -- Merge strategy: prefer non-empty values from new source
                abstract=CASE WHEN length(excluded.abstract) > length(papers.abstract) THEN excluded.abstract ELSE papers.abstract END,
                url=CASE WHEN excluded.url != '' AND papers.url = '' THEN excluded.url ELSE papers.url END,
                metadata_json=excluded.metadata_json,
                citation_count=COALESCE(excluded.citation_count, papers.citation_count),
                doi=COALESCE(excluded.doi, papers.doi),
                venue=CASE WHEN excluded.venue != '' THEN excluded.venue ELSE papers.venue END,
                pdf_url=COALESCE(excluded.pdf_url, papers.pdf_url),
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
                paper.citation_count,
                paper.doi,
                paper.venue,
                paper.pdf_url,
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
        sanitized = _sanitize_fts_query(query)
        try:
            rows = self.conn.execute(
                """SELECT p.* FROM papers_fts fts
                   JOIN papers p ON p.rowid = fts.rowid
                   WHERE papers_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (sanitized, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            # Fallback: quote every token so FTS5 treats them all as literals
            fallback = _quote_all_tokens(query)
            rows = self.conn.execute(
                """SELECT p.* FROM papers_fts fts
                   JOIN papers p ON p.rowid = fts.rowid
                   WHERE papers_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (fallback, limit),
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

    # ── Reading Status ──

    def update_reading_status(self, paper_ids: list[str], status: str) -> int:
        now = datetime.utcnow().isoformat()
        updated = 0
        for pid in paper_ids:
            cur = self.conn.execute(
                "UPDATE papers SET reading_status=?, reading_status_at=?, updated_at=? WHERE id=?",
                (status, now, now, pid),
            )
            updated += cur.rowcount
        self.conn.commit()
        return updated

    def get_reading_stats(self) -> dict[str, int]:
        rows = self.conn.execute(
            "SELECT reading_status, COUNT(*) as cnt FROM papers "
            "WHERE reading_status IS NOT NULL GROUP BY reading_status"
        ).fetchall()
        return {row["reading_status"]: row["cnt"] for row in rows}

    def get_papers_by_reading_status(
        self, status: str | None = None, limit: int = 200
    ) -> list[Paper]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM papers WHERE reading_status=? "
                "ORDER BY reading_status_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM papers WHERE reading_status IS NOT NULL "
                "ORDER BY reading_status_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_paper(r) for r in rows]

    # ── Paper Notes ──

    def save_note(self, note_id: str, paper_id: str, content: str, source: str = "user") -> None:
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            "INSERT INTO paper_notes (id, paper_id, content, source, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET content=?, updated_at=?",
            (note_id, paper_id, content, source, now, now, content, now),
        )
        self.conn.commit()

    def get_notes(self, paper_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM paper_notes WHERE paper_id=? ORDER BY created_at",
            (paper_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Paper Groups ──

    def create_group(self, group_id: str, name: str, description: str = "") -> None:
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            "INSERT INTO paper_groups (id, name, description, created_at, updated_at) VALUES (?,?,?,?,?)",
            (group_id, name, description, now, now),
        )
        self.conn.commit()

    def get_group(self, name: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM paper_groups WHERE name=?", (name,)
        ).fetchone()
        return dict(row) if row else None

    def list_groups(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT g.*, COUNT(gi.paper_id) as paper_count "
            "FROM paper_groups g LEFT JOIN paper_group_items gi ON g.id=gi.group_id "
            "GROUP BY g.id ORDER BY g.updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def add_papers_to_group(self, group_id: str, paper_ids: list[str]) -> int:
        now = datetime.utcnow().isoformat()
        added = 0
        for pid in paper_ids:
            try:
                self.conn.execute(
                    "INSERT INTO paper_group_items (group_id, paper_id, added_at) VALUES (?,?,?)",
                    (group_id, pid, now),
                )
                added += 1
            except sqlite3.IntegrityError:
                pass
        if added:
            self.conn.execute(
                "UPDATE paper_groups SET updated_at=? WHERE id=?", (now, group_id)
            )
        self.conn.commit()
        return added

    def get_group_papers(self, name: str, limit: int = 200) -> list[Paper]:
        rows = self.conn.execute(
            "SELECT p.* FROM papers p "
            "JOIN paper_group_items gi ON p.id=gi.paper_id "
            "JOIN paper_groups g ON g.id=gi.group_id "
            "WHERE g.name=? ORDER BY gi.added_at DESC LIMIT ?",
            (name, limit),
        ).fetchall()
        return [self._row_to_paper(r) for r in rows]

    # ── Paper Contents (v03) ──

    def save_paper_content(self, content: "PaperContent") -> None:
        from paper_agent.domain.models.paper_content import PaperContent  # noqa: F811

        sections = [
            {"name": s.name, "heading": s.heading, "text": s.text, "page_range": list(s.page_range)}
            for s in content.sections
        ]
        tables = [
            {"caption": t.caption, "headers": t.headers, "rows": t.rows, "section": t.section}
            for t in content.tables
        ]
        self.conn.execute(
            """INSERT OR REPLACE INTO paper_contents
            (paper_id, sections_json, tables_json, figure_captions_json, raw_text, parsed_at)
            VALUES (?,?,?,?,?,?)""",
            (
                content.paper_id,
                json.dumps(sections, ensure_ascii=False),
                json.dumps(tables, ensure_ascii=False),
                json.dumps(content.figure_captions, ensure_ascii=False),
                content.raw_text,
                content.parsed_at.isoformat() if content.parsed_at else datetime.utcnow().isoformat(),
            ),
        )
        self.conn.commit()

    def get_paper_content(self, paper_id: str) -> "PaperContent | None":
        from paper_agent.domain.models.paper_content import PaperContent, PaperSection, PaperTable

        row = self.conn.execute(
            "SELECT * FROM paper_contents WHERE paper_id = ?", (paper_id,)
        ).fetchone()
        if not row:
            return None

        sections_raw = json.loads(row["sections_json"])
        tables_raw = json.loads(row["tables_json"])

        return PaperContent(
            paper_id=row["paper_id"],
            sections=[
                PaperSection(
                    name=s["name"], heading=s["heading"], text=s["text"],
                    page_range=tuple(s.get("page_range", [0, 0])),
                )
                for s in sections_raw
            ],
            tables=[
                PaperTable(
                    caption=t["caption"], headers=t["headers"],
                    rows=t["rows"], section=t.get("section", ""),
                )
                for t in tables_raw
            ],
            figure_captions=json.loads(row["figure_captions_json"]),
            raw_text=row["raw_text"],
            parsed_at=datetime.fromisoformat(row["parsed_at"]),
        )

    # ── Paper Profiles (v03) ──

    def save_paper_profile(self, profile: "PaperProfile") -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO paper_profiles
            (paper_id, task, method_family, method_name, datasets_json, baselines_json,
             metrics_json, best_results_json, code_url, venue, compute_cost,
             limitations_json, novelty_claim, problem_formulation, key_contributions_json,
             extracted_from, extracted_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                profile.paper_id,
                profile.task,
                profile.method_family,
                profile.method_name,
                json.dumps(profile.datasets, ensure_ascii=False),
                json.dumps(profile.baselines, ensure_ascii=False),
                json.dumps(profile.metrics, ensure_ascii=False),
                json.dumps(profile.best_results, ensure_ascii=False),
                profile.code_url,
                profile.venue,
                profile.compute_cost,
                json.dumps(profile.limitations, ensure_ascii=False),
                profile.novelty_claim,
                profile.problem_formulation,
                json.dumps(profile.key_contributions, ensure_ascii=False),
                profile.extracted_from,
                profile.extracted_at.isoformat() if profile.extracted_at else datetime.utcnow().isoformat(),
            ),
        )
        self.conn.commit()

    def get_paper_profile(self, paper_id: str) -> "PaperProfile | None":
        from paper_agent.domain.models.paper_profile import PaperProfile

        row = self.conn.execute(
            "SELECT * FROM paper_profiles WHERE paper_id = ?", (paper_id,)
        ).fetchone()
        if not row:
            return None

        return PaperProfile(
            paper_id=row["paper_id"],
            task=row["task"],
            method_family=row["method_family"],
            method_name=row["method_name"],
            datasets=json.loads(row["datasets_json"]),
            baselines=json.loads(row["baselines_json"]),
            metrics=json.loads(row["metrics_json"]),
            best_results=json.loads(row["best_results_json"]),
            code_url=row["code_url"],
            venue=row["venue"],
            compute_cost=row["compute_cost"],
            limitations=json.loads(row["limitations_json"]),
            novelty_claim=row["novelty_claim"] if "novelty_claim" in row.keys() else "",
            problem_formulation=row["problem_formulation"] if "problem_formulation" in row.keys() else "",
            key_contributions=json.loads(row["key_contributions_json"]) if "key_contributions_json" in row.keys() and row["key_contributions_json"] else [],
            extracted_from=row["extracted_from"],
            extracted_at=datetime.fromisoformat(row["extracted_at"]),
        )

    def query_paper_profiles(self, filters: dict[str, str]) -> "list[PaperProfile]":
        from paper_agent.domain.models.paper_profile import PaperProfile

        conditions: list[str] = []
        params: list[str] = []

        for field, value in filters.items():
            if field in ("task", "method_family", "method_name", "venue"):
                conditions.append(f"{field} LIKE ?")
                params.append(f"%{value}%")
            elif field in ("datasets", "baselines", "metrics"):
                conditions.append(f"{field}_json LIKE ?")
                params.append(f"%{value}%")

        where = " AND ".join(conditions) if conditions else "1=1"
        rows = self.conn.execute(
            f"SELECT * FROM paper_profiles WHERE {where}", params
        ).fetchall()

        return [
            PaperProfile(
                paper_id=r["paper_id"],
                task=r["task"],
                method_family=r["method_family"],
                method_name=r["method_name"],
                datasets=json.loads(r["datasets_json"]),
                baselines=json.loads(r["baselines_json"]),
                metrics=json.loads(r["metrics_json"]),
                best_results=json.loads(r["best_results_json"]),
                code_url=r["code_url"],
                venue=r["venue"],
                compute_cost=r["compute_cost"],
                limitations=json.loads(r["limitations_json"]),
                extracted_from=r["extracted_from"],
                extracted_at=datetime.fromisoformat(r["extracted_at"]),
            )
            for r in rows
        ]

    def get_profile_field_stats(self, field: str) -> dict[str, int]:
        from collections import Counter

        valid_fields = {"task", "method_family", "method_name", "venue"}
        if field in valid_fields:
            rows = self.conn.execute(
                f"SELECT {field} FROM paper_profiles WHERE {field} != ''"
            ).fetchall()
            return dict(Counter(r[0] for r in rows).most_common(50))

        if field in ("datasets", "baselines", "metrics"):
            rows = self.conn.execute(
                f"SELECT {field}_json FROM paper_profiles"
            ).fetchall()
            counter: Counter[str] = Counter()
            for r in rows:
                items = json.loads(r[0])
                counter.update(items)
            return dict(counter.most_common(50))

        return {}

    # ── User Feedback (v03) ──

    def save_feedback(
        self, paper_id: str, feedback_type: str, value: str, context: str = ""
    ) -> str:
        import uuid
        fb_id = uuid.uuid4().hex[:12]
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            "INSERT INTO user_feedback (id, paper_id, feedback_type, value, context, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (fb_id, paper_id, feedback_type, value, context, now),
        )
        self.conn.commit()
        return fb_id

    def get_all_feedback(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM user_feedback ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_feedback_for_paper(self, paper_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM user_feedback WHERE paper_id=? ORDER BY created_at",
            (paper_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Watchlist (v03) ──

    def save_watchlist_item(
        self, watch_type: str, watch_value: str, description: str = ""
    ) -> str:
        import uuid
        watch_id = uuid.uuid4().hex[:12]
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            "INSERT INTO watchlist (id, watch_type, watch_value, description, created_at) "
            "VALUES (?,?,?,?,?)",
            (watch_id, watch_type, watch_value, description, now),
        )
        self.conn.commit()
        return watch_id

    def list_watchlist_items(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM watchlist ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_watchlist_item(self, watch_id: str) -> None:
        self.conn.execute("DELETE FROM watchlist WHERE id=?", (watch_id,))
        self.conn.commit()

    def update_watchlist_checked(self, watch_id: str) -> None:
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            "UPDATE watchlist SET last_checked=? WHERE id=?", (now, watch_id)
        )
        self.conn.commit()

    # ── Credibility Assessments (v03) ──

    def save_credibility_assessment(self, assessment: "CredibilityAssessment") -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO credibility_assessments
            (paper_id, code_available, code_url, open_data, venue_tier,
             citation_count, citation_velocity, claim_aggressiveness,
             baseline_completeness, reproducibility_risk, overall_confidence,
             assessment_notes, assessed_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                assessment.paper_id,
                1 if assessment.code_available else (0 if assessment.code_available is not None else None),
                assessment.code_url,
                1 if assessment.open_data else (0 if assessment.open_data is not None else None),
                assessment.venue_tier,
                assessment.citation_count,
                assessment.citation_velocity,
                assessment.claim_aggressiveness,
                assessment.baseline_completeness,
                assessment.reproducibility_risk,
                assessment.overall_confidence,
                assessment.assessment_notes,
                assessment.assessed_at.isoformat() if assessment.assessed_at else datetime.utcnow().isoformat(),
            ),
        )
        self.conn.commit()

    def get_credibility_assessment(self, paper_id: str) -> "CredibilityAssessment | None":
        from paper_agent.domain.models.credibility import CredibilityAssessment

        row = self.conn.execute(
            "SELECT * FROM credibility_assessments WHERE paper_id = ?", (paper_id,)
        ).fetchone()
        if not row:
            return None

        return CredibilityAssessment(
            paper_id=row["paper_id"],
            code_available=bool(row["code_available"]) if row["code_available"] is not None else None,
            code_url=row["code_url"],
            open_data=bool(row["open_data"]) if row["open_data"] is not None else None,
            venue_tier=row["venue_tier"],
            citation_count=row["citation_count"],
            citation_velocity=row["citation_velocity"],
            claim_aggressiveness=row["claim_aggressiveness"],
            baseline_completeness=row["baseline_completeness"],
            reproducibility_risk=row["reproducibility_risk"],
            overall_confidence=row["overall_confidence"],
            assessment_notes=row["assessment_notes"],
            assessed_at=datetime.fromisoformat(row["assessed_at"]),
        )

    # ── Research Context (v03) ──

    def save_research_context(self, context: dict[str, Any]) -> None:
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            """INSERT OR REPLACE INTO research_context
            (id, current_project, current_baseline, current_questions_json,
             active_reading_group, updated_at)
            VALUES (1,?,?,?,?,?)""",
            (
                context.get("current_project", ""),
                context.get("current_baseline", ""),
                json.dumps(context.get("current_questions", []), ensure_ascii=False),
                context.get("active_reading_group", ""),
                now,
            ),
        )
        self.conn.commit()

    def get_research_context(self) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM research_context WHERE id = 1").fetchone()
        if not row:
            return None
        return {
            "current_project": row["current_project"],
            "current_baseline": row["current_baseline"],
            "current_questions": json.loads(row["current_questions_json"]),
            "active_reading_group": row["active_reading_group"],
            "updated_at": row["updated_at"],
        }

    # ── LLM Cache ──

    def get_llm_cache(self, cache_key: str) -> str | None:
        """Get cached LLM response by key. Returns None if not found or expired."""
        row = self.conn.execute(
            "SELECT response_json, expires_at FROM llm_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        if not row:
            return None
        if row["expires_at"]:
            if datetime.fromisoformat(row["expires_at"]) < datetime.utcnow():
                self.conn.execute("DELETE FROM llm_cache WHERE cache_key = ?", (cache_key,))
                self.conn.commit()
                return None
        return row["response_json"]

    def set_llm_cache(
        self,
        cache_key: str,
        provider: str,
        model: str,
        task_type: str,
        input_hash: str,
        response_json: str,
        ttl_hours: int = 168,
    ) -> None:
        """Cache an LLM response. Default TTL: 7 days."""
        now = datetime.utcnow()
        expires = now + __import__("datetime").timedelta(hours=ttl_hours)
        self.conn.execute(
            """INSERT OR REPLACE INTO llm_cache
            (cache_key, provider, model, task_type, input_hash, response_json, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (cache_key, provider, model, task_type, input_hash, response_json,
             now.isoformat(), expires.isoformat()),
        )
        self.conn.commit()

    # ── Internal ──

    def _row_to_paper(self, row: sqlite3.Row) -> Paper:
        pub = row["published_at"]
        keys = row.keys()
        rs = row["reading_status"] if "reading_status" in keys else None
        rs_at = row["reading_status_at"] if "reading_status_at" in keys else None
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
            reading_status=rs,
            reading_status_at=datetime.fromisoformat(rs_at) if rs_at else None,
            citation_count=row["citation_count"] if "citation_count" in keys else None,
            doi=row["doi"] if "doi" in keys else None,
            venue=row["venue"] if "venue" in keys else "",
            pdf_url=row["pdf_url"] if "pdf_url" in keys else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
