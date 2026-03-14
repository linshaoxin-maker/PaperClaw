"""Workspace Layer: manages .paper-agent/ directory of human-readable markdown files."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from paper_agent.infra.storage.sqlite_storage import SQLiteStorage

_JOURNAL_TEMPLATE = """# Research Journal

> Last updated: —
> Entries: 0 (max 50, auto-archived)
"""

_READING_LIST_TEMPLATE = """# Reading List

> Auto-generated from database. Last synced: —

## Important

(none)

## Reading

(none)

## To Read

(none)

## Read

(none)
"""

_COLLECTION_INDEX_TEMPLATE = """# Paper Collections

> Auto-generated index. Last synced: —

(no collections yet)
"""


class WorkspaceManager:
    """Manages the .paper-agent/ workspace directory."""

    DIRS = ("collections", "notes", "citation-traces")
    FILES = ("research-journal.md", "reading-list.md")

    def __init__(self, workspace_dir: Path, storage: SQLiteStorage) -> None:
        self._root = workspace_dir
        self._storage = storage

    @property
    def root(self) -> Path:
        return self._root

    # ── Init ──

    def is_initialized(self) -> bool:
        return self._root.is_dir() and (self._root / "research-journal.md").exists()

    def init(self) -> dict[str, Any]:
        if self.is_initialized():
            missing = self._ensure_complete()
            if not missing:
                return {"status": "already_initialized", "path": str(self._root)}
            return {"status": "repaired", "path": str(self._root), "files_created": missing}

        self._root.mkdir(parents=True, exist_ok=True)
        created: list[str] = []

        for d in self.DIRS:
            (self._root / d).mkdir(exist_ok=True)
            created.append(f"{d}/")

        (self._root / "research-journal.md").write_text(_JOURNAL_TEMPLATE, encoding="utf-8")
        created.append("research-journal.md")

        (self._root / "reading-list.md").write_text(_READING_LIST_TEMPLATE, encoding="utf-8")
        created.append("reading-list.md")

        idx = self._root / "collections" / "_index.md"
        idx.write_text(_COLLECTION_INDEX_TEMPLATE, encoding="utf-8")
        created.append("collections/_index.md")

        return {"status": "initialized", "path": str(self._root), "files_created": created}

    def _ensure_complete(self) -> list[str]:
        created: list[str] = []
        for d in self.DIRS:
            dp = self._root / d
            if not dp.is_dir():
                dp.mkdir(parents=True, exist_ok=True)
                created.append(f"{d}/")
        for f in self.FILES:
            fp = self._root / f
            if not fp.exists():
                template = _JOURNAL_TEMPLATE if "journal" in f else _READING_LIST_TEMPLATE
                fp.write_text(template, encoding="utf-8")
                created.append(f)
        idx = self._root / "collections" / "_index.md"
        if not idx.exists():
            idx.write_text(_COLLECTION_INDEX_TEMPLATE, encoding="utf-8")
            created.append("collections/_index.md")
        return created

    # ── Journal ──

    def append_journal(self, summary: str, details: dict[str, Any] | None = None) -> None:
        if not self.is_initialized():
            return
        path = self._root / "research-journal.md"
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")

        entry_lines = [f"### {time_str} — {summary}"]
        if details:
            for k, v in details.items():
                entry_lines.append(f"- {k}: {v}")
        entry_text = "\n".join(entry_lines)

        content = path.read_text(encoding="utf-8")
        date_header = f"## {date_str}"

        if date_header in content:
            content = content.replace(date_header, f"{date_header}\n\n{entry_text}\n", 1)
        else:
            insert_pos = content.find("\n## ")
            if insert_pos == -1:
                content = content.rstrip() + f"\n\n{date_header}\n\n{entry_text}\n"
            else:
                content = (
                    content[:insert_pos]
                    + f"\n{date_header}\n\n{entry_text}\n"
                    + content[insert_pos:]
                )

        entry_count = len(re.findall(r"^### \d{2}:\d{2}", content, re.MULTILINE))
        header = (
            f"# Research Journal\n\n"
            f"> Last updated: {now.strftime('%Y-%m-%d %H:%M')}\n"
            f"> Entries: {entry_count} (max 50, auto-archived)\n"
        )
        content = re.sub(
            r"^# Research Journal.*?(?=\n## |\Z)",
            header,
            content,
            count=1,
            flags=re.DOTALL,
        )

        path.write_text(content, encoding="utf-8")

        if entry_count > 50:
            self._trim_journal(content, path)

    def _trim_journal(self, content: str, path: Path) -> None:
        sections = re.split(r"(?=^## \d{4}-\d{2}-\d{2})", content, flags=re.MULTILINE)
        header = sections[0] if sections else ""
        dated = [s for s in sections[1:] if s.strip()]
        if len(dated) <= 2:
            return

        keep = dated[:2]
        archive = dated[2:]

        path.write_text(header + "".join(keep), encoding="utf-8")

        archive_path = self._root / "research-journal-archive.md"
        existing = archive_path.read_text(encoding="utf-8") if archive_path.exists() else ""
        archive_path.write_text(existing + "\n".join(archive), encoding="utf-8")

    # ── Reading List ──

    def rebuild_reading_list(self) -> None:
        if not self.is_initialized():
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        sections: dict[str, list[str]] = {
            "important": [], "reading": [], "to_read": [], "read": [],
        }
        papers = self._storage.get_papers_by_reading_status(limit=500)
        for p in papers:
            if p.reading_status and p.reading_status in sections:
                line = f"- [{p.title}]({p.url}) `{p.id}` — {p.source_name}"
                if p.relevance_score:
                    line += f" (score: {p.relevance_score:.1f})"
                sections[p.reading_status].append(line)

        lines = [
            "# Reading List\n",
            f"> Auto-generated from database. Last synced: {now}\n",
        ]
        display = {"important": "Important", "reading": "Reading", "to_read": "To Read", "read": "Read"}
        for key, label in display.items():
            lines.append(f"\n## {label}\n")
            if sections[key]:
                lines.extend(sections[key])
            else:
                lines.append("(none)")
            lines.append("")

        (self._root / "reading-list.md").write_text("\n".join(lines), encoding="utf-8")

    # ── Notes ──

    def sync_note_file(self, paper_id: str) -> Path | None:
        if not self.is_initialized():
            return None
        paper = self._storage.get_paper(paper_id)
        if not paper:
            return None
        notes = self._storage.get_notes(paper_id)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        lines = [
            f"# {paper.title}\n",
            f"> Paper ID: `{paper.id}`",
            f"> Source: {paper.source_name} | URL: {paper.url}",
            f"> Last synced: {now}\n",
        ]

        if paper.abstract:
            lines.append("## Abstract\n")
            lines.append(paper.abstract[:500])
            lines.append("")

        for note in notes:
            source_label = "AI Analysis" if note["source"] == "ai_analysis" else "Note"
            ts = note["created_at"][:16] if note.get("created_at") else ""
            lines.append(f"## {source_label} ({ts})\n")
            lines.append(note["content"])
            lines.append("")

        path = self._root / "notes" / f"{paper_id}.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    # ── Collections / Groups ──

    def sync_collection_file(self, name: str) -> Path | None:
        if not self.is_initialized():
            return None
        group = self._storage.get_group(name)
        if not group:
            return None
        papers = self._storage.get_group_papers(name)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        lines = [
            f"# Collection: {name}\n",
            f"> {group.get('description', '')}",
            f"> Papers: {len(papers)} | Last synced: {now}\n",
        ]
        for p in papers:
            line = f"- [{p.title}]({p.url}) `{p.id}`"
            if p.relevance_score:
                line += f" (score: {p.relevance_score:.1f})"
            lines.append(line)

        if not papers:
            lines.append("(no papers yet)")

        safe_name = re.sub(r"[^\w\-]", "_", name)
        path = self._root / "collections" / f"{safe_name}.md"
        path.write_text("\n".join(lines), encoding="utf-8")

        self.rebuild_collection_index()
        return path

    def rebuild_collection_index(self) -> None:
        if not self.is_initialized():
            return
        groups = self._storage.list_groups()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            "# Paper Collections\n",
            f"> Auto-generated index. Last synced: {now}\n",
        ]
        if groups:
            for g in groups:
                safe = re.sub(r"[^\w\-]", "_", g["name"])
                lines.append(
                    f"- [{g['name']}]({safe}.md) — {g.get('description', '')} "
                    f"({g.get('paper_count', 0)} papers)"
                )
        else:
            lines.append("(no collections yet)")

        (self._root / "collections" / "_index.md").write_text(
            "\n".join(lines), encoding="utf-8"
        )

    # ── Citation Traces ──

    def update_citation_trace(
        self,
        trace_name: str,
        paper_id: str,
        paper_title: str,
        references: list[dict[str, str]],
        citations: list[dict[str, str]],
    ) -> Path | None:
        if not self.is_initialized():
            return None
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        safe_name = re.sub(r"[^\w\-]", "_", trace_name)
        path = self._root / "citation-traces" / f"{safe_name}.md"

        new_section = [
            f"\n## {paper_title} `{paper_id}` ({now})\n",
        ]
        if references:
            new_section.append("### References (this paper cites)\n")
            for r in references[:20]:
                new_section.append(f"- {r.get('title', 'Unknown')} — {r.get('url', '')}")
        if citations:
            new_section.append("\n### Cited by\n")
            for c in citations[:20]:
                new_section.append(f"- {c.get('title', 'Unknown')} — {c.get('url', '')}")
        new_section.append("")

        if path.exists():
            existing = path.read_text(encoding="utf-8")
            header_end = existing.find("\n## ")
            if header_end == -1:
                content = existing.rstrip() + "\n" + "\n".join(new_section)
            else:
                content = existing[:header_end] + "\n".join(new_section) + existing[header_end:]
        else:
            content = (
                f"# Citation Trace: {trace_name}\n\n"
                f"> Last updated: {now}\n"
                + "\n".join(new_section)
            )

        path.write_text(content, encoding="utf-8")
        return path

    # ── Context Recovery ──

    def get_context(self) -> dict[str, Any]:
        result: dict[str, Any] = {"initialized": self.is_initialized()}
        if not self.is_initialized():
            return result

        journal_path = self._root / "research-journal.md"
        if journal_path.exists():
            text = journal_path.read_text(encoding="utf-8")
            entries = re.findall(r"^### .+", text, re.MULTILINE)
            result["journal_recent"] = entries[:10]

        result["reading_stats"] = self._storage.get_reading_stats()

        groups = self._storage.list_groups()
        result["collections"] = [
            {"name": g["name"], "papers": g.get("paper_count", 0)} for g in groups
        ]

        traces_dir = self._root / "citation-traces"
        if traces_dir.is_dir():
            result["citation_traces"] = [
                f.stem for f in traces_dir.glob("*.md")
            ]

        return result

    # ── Rebuild All ──

    def rebuild_all(self) -> dict[str, Any]:
        self.init()
        self.rebuild_reading_list()

        groups = self._storage.list_groups()
        for g in groups:
            self.sync_collection_file(g["name"])

        papers_with_notes = set()
        for row in self._storage.conn.execute(
            "SELECT DISTINCT paper_id FROM paper_notes"
        ).fetchall():
            papers_with_notes.add(row["paper_id"])
        for pid in papers_with_notes:
            self.sync_note_file(pid)

        return {
            "status": "rebuilt",
            "reading_list": True,
            "collections": len(groups),
            "notes": len(papers_with_notes),
        }
