"""Workspace Layer: manages .paper-agent/ directory of human-readable markdown files.

Directory structure (Obsidian-friendly):

    .paper-agent/
    ├── .data/                    ← system files (hidden in Obsidian)
    │   ├── config.yaml
    │   ├── library.db
    │   ├── sources.yaml
    │   └── artifacts/
    ├── 00-Dashboard.md           ← home dashboard
    ├── 01-每日推荐/
    ├── 02-论文库/                ← all papers (sync_vault output)
    ├── 03-深度分析/
    ├── 04-对比分析/
    ├── 05-文献综述/
    ├── 06-趋势洞察/
    ├── 07-阅读包/
    ├── 08-研究Ideas/
    ├── 09-实验计划/
    ├── 10-引用追踪/
    ├── 11-论文分组/
    ├── 12-搜索结果/
    ├── 13-筛选报告/
    ├── 阅读清单.md
    └── 研究日志.md
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from paper_agent.infra.storage.sqlite_storage import SQLiteStorage

_JOURNAL_TEMPLATE = """# 研究日志

> Last updated: —
> Entries: 0 (max 50, auto-archived)
"""

_READING_LIST_TEMPLATE = """# 阅读清单

> Auto-generated from database. Last synced: —

## ⭐ 重要

(none)

## 📖 阅读中

(none)

## 📋 待读

(none)

## ✅ 已读

(none)
"""

_COLLECTION_INDEX_TEMPLATE = """# 论文分组

> Auto-generated index. Last synced: —

(暂无分组)
"""


# Map report_type → subdirectory name (new numbered Chinese dirs)
_REPORT_TYPE_MAP: dict[str, str] = {
    "daily_digest": "01-每日推荐",
    "triage": "13-筛选报告",
    "survey": "05-文献综述",
    "insight": "06-趋势洞察",
    "comparison": "04-对比分析",
    "analysis": "03-深度分析",
    "citation_map": "10-引用追踪",
    "reading_pack": "07-阅读包",
    "ideation": "08-研究Ideas",
    "experiment_plan": "09-实验计划",
    "search_result": "12-搜索结果",
}


class WorkspaceManager:
    """Manages the .paper-agent/ workspace directory (Obsidian-friendly)."""

    DIRS = (
        "01-每日推荐", "02-论文库", "03-深度分析", "04-对比分析",
        "05-文献综述", "06-趋势洞察", "07-阅读包", "08-研究Ideas",
        "09-实验计划", "10-引用追踪", "11-论文分组", "12-搜索结果",
        "13-筛选报告",
    )
    JOURNAL_FILE = "研究日志.md"
    READING_LIST_FILE = "阅读清单.md"
    DASHBOARD_FILE = "00-Dashboard.md"

    def __init__(self, workspace_dir: Path, storage: SQLiteStorage | None = None) -> None:
        self._root = workspace_dir
        self._storage = storage

    @property
    def root(self) -> Path:
        return self._root

    # ── Init ──

    def is_initialized(self) -> bool:
        return self._root.is_dir() and (self._root / self.JOURNAL_FILE).exists()

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

        (self._root / self.JOURNAL_FILE).write_text(_JOURNAL_TEMPLATE, encoding="utf-8")
        created.append(self.JOURNAL_FILE)

        (self._root / self.READING_LIST_FILE).write_text(_READING_LIST_TEMPLATE, encoding="utf-8")
        created.append(self.READING_LIST_FILE)

        idx = self._root / "11-论文分组" / "_index.md"
        idx.write_text(_COLLECTION_INDEX_TEMPLATE, encoding="utf-8")
        created.append("11-论文分组/_index.md")

        # Generate Obsidian config for best experience
        self._init_obsidian_config()
        created.append(".obsidian/")

        # Generate Dataview query pages
        self._init_query_pages()
        created.append("query pages")

        # Generate initial dashboard
        self.rebuild_dashboard()
        created.append(self.DASHBOARD_FILE)

        return {"status": "initialized", "path": str(self._root), "files_created": created}

    def _ensure_complete(self) -> list[str]:
        created: list[str] = []
        for d in self.DIRS:
            dp = self._root / d
            if not dp.is_dir():
                dp.mkdir(parents=True, exist_ok=True)
                created.append(f"{d}/")
        for fname, template in [
            (self.JOURNAL_FILE, _JOURNAL_TEMPLATE),
            (self.READING_LIST_FILE, _READING_LIST_TEMPLATE),
        ]:
            fp = self._root / fname
            if not fp.exists():
                fp.write_text(template, encoding="utf-8")
                created.append(fname)
        idx = self._root / "11-论文分组" / "_index.md"
        if not idx.exists():
            idx.write_text(_COLLECTION_INDEX_TEMPLATE, encoding="utf-8")
            created.append("11-论文分组/_index.md")
        return created

    def ensure_initialized(self) -> None:
        """Auto-init if not yet initialized. Called by MCP tools silently."""
        if not self.is_initialized():
            self.init()

    def _init_obsidian_config(self) -> None:
        """Generate .obsidian/ config for optimal paper browsing experience."""
        import json as _json

        obs_dir = self._root / ".obsidian"
        obs_dir.mkdir(exist_ok=True)

        # App config: enable wikilinks, set default new file location
        app_config = {
            "useMarkdownLinks": False,  # Use [[wikilinks]]
            "newFileLocation": "folder",
            "newFileFolderPath": "02-论文库",
            "attachmentFolderPath": ".data/attachments",
            "showUnsupportedFiles": False,
            "defaultViewMode": "preview",
            "readableLineLength": True,
            "strictLineBreaks": False,
        }
        (obs_dir / "app.json").write_text(
            _json.dumps(app_config, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Appearance: clean theme
        appearance = {
            "accentColor": "#7c5cfc",
            "interfaceFontSize": 15,
        }
        (obs_dir / "appearance.json").write_text(
            _json.dumps(appearance, indent=2), encoding="utf-8"
        )

        # Community plugins list (user still needs to install them manually)
        # Pre-register so they're enabled once installed
        (obs_dir / "community-plugins.json").write_text(
            _json.dumps(["dataview", "calendar"], indent=2), encoding="utf-8"
        )

        # Graph view config: color by folder
        graph_config = {
            "collapse-filter": False,
            "search": "",
            "showTags": True,
            "showAttachments": False,
            "hideUnresolved": False,
            "showOrphans": True,
            "collapse-color-groups": False,
            "colorGroups": [
                {"query": "path:02-论文库", "color": {"a": 1, "rgb": 5145596}},
                {"query": "path:01-每日推荐", "color": {"a": 1, "rgb": 16744448}},
                {"query": "path:05-文献综述", "color": {"a": 1, "rgb": 65280}},
                {"query": "path:03-深度分析", "color": {"a": 1, "rgb": 16776960}},
            ],
            "collapse-display": False,
            "lineSizeMultiplier": 1,
            "nodeSizeMultiplier": 1,
            "collapse-forces": False,
            "centerStrength": 0.518713248970312,
            "repelStrength": 10,
            "linkStrength": 1,
            "linkDistance": 250,
        }
        (obs_dir / "graph.json").write_text(
            _json.dumps(graph_config, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Starred / bookmarks: pin dashboard
        bookmarks = {
            "items": [
                {"type": "file", "ctime": 0, "path": "00-Dashboard.md"},
                {"type": "file", "ctime": 0, "path": "阅读清单.md"},
                {"type": "file", "ctime": 0, "path": "研究日志.md"},
            ]
        }
        (obs_dir / "bookmarks.json").write_text(
            _json.dumps(bookmarks, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _init_query_pages(self) -> None:
        """Generate pre-built Dataview query pages for common views."""
        vault_dir = self._root / "02-论文库"
        vault_dir.mkdir(exist_ok=True)

        (vault_dir / "_按方法分类.md").write_text("""# 📊 按方法分类

```dataview
TABLE first_author as "一作", year as "年份", score as "分数"
FROM "02-论文库"
WHERE !startswith(file.name, "_")
FLATTEN tags as tag
WHERE startswith(tag, "topic/")
SORT tag ASC, score DESC
```
""", encoding="utf-8")

        (vault_dir / "_按年份分布.md").write_text("""# 📅 按年份分布

```dataview
TABLE first_author as "一作", score as "分数", status as "状态"
FROM "02-论文库"
WHERE !startswith(file.name, "_")
SORT year DESC, score DESC
```
""", encoding="utf-8")

        (vault_dir / "_按会议分类.md").write_text("""# 🏛️ 按来源分类

```dataview
TABLE first_author as "一作", year as "年份", score as "分数"
FROM "02-论文库"
WHERE !startswith(file.name, "_")
SORT source ASC, score DESC
```
""", encoding="utf-8")

        (vault_dir / "_最近入库.md").write_text("""# 🆕 最近入库

```dataview
TABLE first_author as "一作", year as "年份", score as "分数", source as "来源"
FROM "02-论文库"
WHERE !startswith(file.name, "_")
SORT file.ctime DESC
LIMIT 50
```
""", encoding="utf-8")

        (vault_dir / "_高分论文.md").write_text("""# ⭐ 高分论文

```dataview
TABLE first_author as "一作", year as "年份", score as "分数", status as "状态"
FROM "02-论文库"
WHERE !startswith(file.name, "_") AND score > 0
SORT score DESC
```

> 💡 score 为 0 的论文还没经过评分。对 Claude 说"帮我给论文打分"即可。
""", encoding="utf-8")

        (vault_dir / "_阅读进度.md").write_text("""# 📖 阅读进度

## ⭐ 重要
```dataview
TABLE first_author as "一作", score as "分数"
FROM "02-论文库"
WHERE status = "important"
SORT score DESC
```

## 📖 阅读中
```dataview
TABLE first_author as "一作", score as "分数"
FROM "02-论文库"
WHERE status = "reading"
SORT score DESC
```

## 📋 待读
```dataview
TABLE first_author as "一作", score as "分数"
FROM "02-论文库"
WHERE status = "to_read"
SORT score DESC
```

## ✅ 已读
```dataview
TABLE first_author as "一作", score as "分数"
FROM "02-论文库"
WHERE status = "read"
SORT score DESC
```

## 📥 全部论文
```dataview
TABLE first_author as "一作", year as "年份", score as "分数", status as "状态"
FROM "02-论文库"
WHERE !startswith(file.name, "_")
SORT score DESC
```
""", encoding="utf-8")

    def rebuild_query_pages(self) -> None:
        """Rebuild static query pages from database. Called after paper_sync_vault."""
        if not self._storage or not self.is_initialized():
            return

        vault_dir = self._root / "02-论文库"
        vault_dir.mkdir(exist_ok=True)

        papers = self._storage.conn.execute(
            "SELECT id, title, source_paper_id, relevance_score, reading_status, "
            "published_at, topics_json, source_name, venue FROM papers "
            "ORDER BY relevance_score DESC"
        ).fetchall()

        # Helper: build wikilink from db row
        def _link(row):
            src = re.sub(r"[/\\:]", "_", (row["source_paper_id"] or "")).strip()
            slug = re.sub(r"[^\w\s-]", "", row["title"])[:80].strip().replace(" ", "_")
            fname = f"{src}_{slug}" if (src and src != row["id"]) else slug
            return f"[[02-论文库/{fname}|{row['title'][:60]}]]"

        def _year(row):
            pa = row["published_at"]
            if not pa:
                return "N/A"
            return str(pa)[:4]

        def _topics(row):
            t = row["topics_json"]
            if not t:
                return ""
            # topics stored as JSON string or comma-separated
            import json as _j
            try:
                lst = _j.loads(t) if t.startswith("[") else [x.strip() for x in t.split(",")]
            except Exception:
                lst = [t]
            return ", ".join(lst[:3])

        # ── 高分论文 ──
        lines = ["# ⭐ 高分论文 (score ≥ 8)\n"]
        lines.append("| 论文 | 一作 | 年份 | 分数 | 状态 |")
        lines.append("|------|------|------|------|------|")
        for p in papers:
            if (p["relevance_score"] or 0) >= 8:
                lines.append(
                    f"| {_link(p)} | — | {_year(p)} | {p['relevance_score']} | {p['reading_status'] or 'unread'} |"
                )
        if len(lines) == 3:
            lines.append("| (暂无 score ≥ 8 的论文) | | | | |")
        (vault_dir / "_高分论文.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

        # ── 按方法分类 ──
        method_groups: dict[str, list] = {}
        for p in papers:
            for topic in (_topics(p) or "未分类").split(", "):
                topic = topic.strip() or "未分类"
                method_groups.setdefault(topic, []).append(p)
        lines = ["# 📊 按方法/主题分类\n"]
        for method, plist in sorted(method_groups.items(), key=lambda x: -len(x[1])):
            lines.append(f"## {method} ({len(plist)} 篇)\n")
            for p in plist[:20]:
                lines.append(f"- {_link(p)} (score: {p['relevance_score'] or 0})")
            if len(plist) > 20:
                lines.append(f"- ... 还有 {len(plist) - 20} 篇")
            lines.append("")
        (vault_dir / "_按方法分类.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

        # ── 按年份分布 ──
        year_groups: dict[str, list] = {}
        for p in papers:
            y = _year(p)
            year_groups.setdefault(y, []).append(p)
        lines = ["# 📅 按年份分布\n"]
        lines.append("| 年份 | 论文数 |")
        lines.append("|------|--------|")
        for y in sorted(year_groups.keys(), reverse=True):
            lines.append(f"| {y} | {len(year_groups[y])} |")
        lines.append("")
        for y in sorted(year_groups.keys(), reverse=True):
            lines.append(f"## {y} ({len(year_groups[y])} 篇)\n")
            for p in year_groups[y][:15]:
                lines.append(f"- {_link(p)} (score: {p['relevance_score'] or 0})")
            if len(year_groups[y]) > 15:
                lines.append(f"- ... 还有 {len(year_groups[y]) - 15} 篇")
            lines.append("")
        (vault_dir / "_按年份分布.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

        # ── 按会议分类 ──
        # venue info is in topics for some sources
        lines = ["# 🏛️ 按来源分类\n"]
        source_groups: dict[str, list] = {}
        for p in papers:
            src = p["source_name"] or "unknown"
            source_groups.setdefault(src, []).append(p)
        for src, plist in sorted(source_groups.items(), key=lambda x: -len(x[1])):
            lines.append(f"## {src} ({len(plist)} 篇)\n")
            for p in plist[:15]:
                lines.append(f"- {_link(p)} (score: {p['relevance_score'] or 0}, {_year(p)})")
            if len(plist) > 15:
                lines.append(f"- ... 还有 {len(plist) - 15} 篇")
            lines.append("")
        (vault_dir / "_按会议分类.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

        # ── 最近入库 ──
        recent = papers[:50]  # already sorted by score, re-sort by date
        recent_sorted = sorted(recent, key=lambda p: p["published_at"] or "", reverse=True)
        lines = ["# 🆕 最近入库 (Top 50)\n"]
        lines.append("| 论文 | 年份 | 分数 | 来源 |")
        lines.append("|------|------|------|------|")
        for p in recent_sorted:
            lines.append(f"| {_link(p)} | {_year(p)} | {p['relevance_score'] or 0} | {p['source_name'] or ''} |")
        (vault_dir / "_最近入库.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

        # ── 阅读进度 ──
        status_groups: dict[str, list] = {"important": [], "reading": [], "to_read": [], "read": [], "unread": []}
        for p in papers:
            s = p["reading_status"] or "unread"
            status_groups.setdefault(s, []).append(p)
        display = {
            "important": "⭐ 重要",
            "reading": "📖 阅读中",
            "to_read": "📋 待读",
            "read": "✅ 已读",
            "unread": "📥 未读",
        }
        lines = ["# 📖 阅读进度\n"]
        lines.append("| 状态 | 数量 |")
        lines.append("|------|------|")
        for key, label in display.items():
            lines.append(f"| {label} | {len(status_groups.get(key, []))} |")
        lines.append("")
        for key, label in display.items():
            plist = status_groups.get(key, [])
            if not plist:
                continue
            lines.append(f"## {label} ({len(plist)} 篇)\n")
            for p in plist[:30]:
                lines.append(f"- {_link(p)} (score: {p['relevance_score'] or 0})")
            if len(plist) > 30:
                lines.append(f"- ... 还有 {len(plist) - 30} 篇")
            lines.append("")
        (vault_dir / "_阅读进度.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ── Dashboard ──

    def rebuild_dashboard(self) -> None:
        """Regenerate 00-Dashboard.md with static content from database."""
        if not self.is_initialized():
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        lines = [
            "# 📊 Research Dashboard\n",
            f"> Last updated: {now}",
            "> 此文件由 paper-agent 自动生成\n",
        ]

        # Stats from DB
        if self._storage:
            stats = self._storage.get_reading_stats()
            total = stats.get("total", 0)
            to_read = stats.get("to_read", 0)
            reading = stats.get("reading", 0)
            read = stats.get("read", 0)
            important = stats.get("important", 0)

            lines.append("## 📈 论文库概览\n")
            lines.append(f"| 总计 | 待读 | 阅读中 | 已读 | ⭐重要 |")
            lines.append(f"|------|------|--------|------|--------|")
            lines.append(f"| {total} | {to_read} | {reading} | {read} | {important} |\n")

        # Link to query pages
        lines.append("## 📂 快速导航\n")
        lines.append("- [[02-论文库/_高分论文|⭐ 高分论文]]")
        lines.append("- [[02-论文库/_按方法分类|📊 按方法分类]]")
        lines.append("- [[02-论文库/_按年份分布|📅 按年份分布]]")
        lines.append("- [[02-论文库/_按会议分类|🏛️ 按来源分类]]")
        lines.append("- [[02-论文库/_最近入库|🆕 最近入库]]")
        lines.append("- [[02-论文库/_阅读进度|📖 阅读进度]]")
        lines.append("- [[阅读清单|📋 阅读清单]]")
        lines.append("- [[研究日志|📝 研究日志]]")
        lines.append("")

        # List reports from each directory
        report_dirs = {
            "01-每日推荐": "📅 每日推荐",
            "05-文献综述": "📚 文献综述",
            "04-对比分析": "⚖️ 对比分析",
            "03-深度分析": "📝 深度分析",
            "06-趋势洞察": "📊 趋势洞察",
            "07-阅读包": "📦 阅读包",
            "08-研究Ideas": "💡 研究 Ideas",
            "09-实验计划": "🧪 实验计划",
            "10-引用追踪": "🔗 引用追踪",
            "12-搜索结果": "🔍 搜索结果",
            "13-筛选报告": "📋 筛选报告",
        }
        has_reports = False
        for subdir, label in report_dirs.items():
            d = self._root / subdir
            if d.is_dir():
                files = sorted(
                    [f for f in d.glob("*.md") if not f.name.startswith("_")],
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                if files:
                    if not has_reports:
                        lines.append("## 📄 研究报告\n")
                        has_reports = True
                    lines.append(f"### {label} ({len(files)} 份)\n")
                    for f in files[:5]:
                        lines.append(f"- [[{subdir}/{f.stem}]]")
                    if len(files) > 5:
                        lines.append(f"- ... 还有 {len(files) - 5} 份")
                    lines.append("")

        # Collections
        if self._storage:
            groups = self._storage.list_groups()
            if groups:
                lines.append("## 📁 论文分组\n")
                for g in groups:
                    safe = re.sub(r"[^\w\-]", "_", g["name"])
                    lines.append(
                        f"- [[11-论文分组/{safe}|{g['name']}]] "
                        f"({g.get('paper_count', 0)} 篇)"
                    )
                lines.append("")

        # Journal recent
        journal_path = self._root / self.JOURNAL_FILE
        if journal_path.exists():
            text = journal_path.read_text(encoding="utf-8")
            entries = re.findall(r"^### (.+)", text, re.MULTILINE)
            if entries:
                lines.append("## 🕐 最近活动\n")
                for e in entries[:8]:
                    lines.append(f"- {e}")
                lines.append("")

        lines.append("---\n")
        lines.append("*此文件由 paper-agent 自动生成，请勿手动编辑。*\n")

        (self._root / self.DASHBOARD_FILE).write_text("\n".join(lines), encoding="utf-8")

    # ── Journal ──

    def append_journal(self, summary: str, details: dict[str, Any] | None = None) -> None:
        if not self.is_initialized():
            return
        path = self._root / self.JOURNAL_FILE
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
            f"# 研究日志\n\n"
            f"> Last updated: {now.strftime('%Y-%m-%d %H:%M')}\n"
            f"> Entries: {entry_count} (max 50, auto-archived)\n"
        )
        content = re.sub(
            r"^# 研究日志.*?(?=\n## |\Z)",
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

        archive_path = self._root / "研究日志-归档.md"
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
                line = f"- [[02-论文库/{self._paper_filename(p)}|{p.title}]]"
                if p.relevance_score:
                    line += f" (score: {p.relevance_score:.1f})"
                sections[p.reading_status].append(line)

        lines = [
            "# 阅读清单\n",
            f"> Auto-generated from database. Last synced: {now}\n",
        ]
        display = {
            "important": "⭐ 重要",
            "reading": "📖 阅读中",
            "to_read": "📋 待读",
            "read": "✅ 已读",
        }
        for key, label in display.items():
            lines.append(f"\n## {label}\n")
            if sections[key]:
                lines.extend(sections[key])
            else:
                lines.append("(none)")
            lines.append("")

        (self._root / self.READING_LIST_FILE).write_text("\n".join(lines), encoding="utf-8")

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

        path = self._root / "03-深度分析" / f"{paper_id}.md"
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
            f"# 分组: {name}\n",
            f"> {group.get('description', '')}",
            f"> Papers: {len(papers)} | Last synced: {now}\n",
        ]
        for p in papers:
            line = f"- [[02-论文库/{self._paper_filename(p)}|{p.title}]]"
            if p.relevance_score:
                line += f" (score: {p.relevance_score:.1f})"
            lines.append(line)

        if not papers:
            lines.append("(暂无论文)")

        safe_name = re.sub(r"[^\w\-]", "_", name)
        path = self._root / "11-论文分组" / f"{safe_name}.md"
        path.write_text("\n".join(lines), encoding="utf-8")

        self.rebuild_collection_index()
        return path

    def rebuild_collection_index(self) -> None:
        if not self.is_initialized():
            return
        groups = self._storage.list_groups()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            "# 论文分组\n",
            f"> Auto-generated index. Last synced: {now}\n",
        ]
        if groups:
            for g in groups:
                safe = re.sub(r"[^\w\-]", "_", g["name"])
                lines.append(
                    f"- [[11-论文分组/{safe}|{g['name']}]] — {g.get('description', '')} "
                    f"({g.get('paper_count', 0)} papers)"
                )
        else:
            lines.append("(暂无分组)")

        (self._root / "11-论文分组" / "_index.md").write_text(
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
        path = self._root / "10-引用追踪" / f"{safe_name}.md"

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
                f"# 引用追踪: {trace_name}\n\n"
                f"> Last updated: {now}\n"
                + "\n".join(new_section)
            )

        path.write_text(content, encoding="utf-8")
        return path

    # ── Reports ──

    def save_report(
        self,
        report_type: str,
        content: str,
        filename: str | None = None,
    ) -> Path:
        """Save a structured report to the appropriate subdirectory.

        Returns the path of the written file.
        Raises ValueError for unknown report types.
        """
        self.ensure_initialized()
        subdir = _REPORT_TYPE_MAP.get(report_type)
        if subdir is None:
            raise ValueError(
                f"Unknown report_type '{report_type}'. "
                f"Valid types: {', '.join(sorted(_REPORT_TYPE_MAP))}"
            )

        target_dir = self._root / subdir
        target_dir.mkdir(parents=True, exist_ok=True)

        if filename:
            safe = re.sub(r"[^\w\-.]", "_", filename)
            if not safe.endswith(".md"):
                safe += ".md"
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            safe = f"{today}.md"

        path = target_dir / safe
        path.write_text(content, encoding="utf-8")

        label_map = {
            "daily_digest": "每日推荐",
            "triage": "筛选报告",
            "survey": "文献综述",
            "insight": "趋势洞察",
            "comparison": "对比分析",
            "analysis": "深度分析",
            "citation_map": "引用追踪",
            "reading_pack": "阅读包",
            "ideation": "研究 Ideas",
            "experiment_plan": "实验计划",
            "search_result": "搜索结果",
        }
        label = label_map.get(report_type, report_type)
        self.append_journal(
            f"保存{label}: {path.name}",
            {"路径": str(path.relative_to(self._root)), "类型": report_type},
        )
        return path

    def list_reports(self, report_type: str | None = None) -> list[dict[str, Any]]:
        """List saved reports, optionally filtered by type."""
        if not self.is_initialized():
            return []

        types_to_scan: dict[str, str]
        if report_type:
            subdir = _REPORT_TYPE_MAP.get(report_type)
            if subdir is None:
                return []
            types_to_scan = {report_type: subdir}
        else:
            types_to_scan = dict(_REPORT_TYPE_MAP)

        results: list[dict[str, Any]] = []
        for rtype, subdir in types_to_scan.items():
            d = self._root / subdir
            if not d.is_dir():
                continue
            for f in sorted(d.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
                if f.name.startswith("_"):
                    continue
                results.append({
                    "type": rtype,
                    "filename": f.name,
                    "path": str(f),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                })
        return results

    # ── Context Recovery ──

    def get_context(self) -> dict[str, Any]:
        result: dict[str, Any] = {"initialized": self.is_initialized()}
        if not self.is_initialized():
            return result

        journal_path = self._root / self.JOURNAL_FILE
        if journal_path.exists():
            text = journal_path.read_text(encoding="utf-8")
            entries = re.findall(r"^### .+", text, re.MULTILINE)
            result["journal_recent"] = entries[:10]

        result["reading_stats"] = self._storage.get_reading_stats()

        groups = self._storage.list_groups()
        result["collections"] = [
            {"name": g["name"], "papers": g.get("paper_count", 0)} for g in groups
        ]

        traces_dir = self._root / "10-引用追踪"
        if traces_dir.is_dir():
            result["citation_traces"] = [
                f.stem for f in traces_dir.glob("*.md")
            ]

        report_counts: dict[str, int] = {}
        for rtype, subdir in _REPORT_TYPE_MAP.items():
            d = self._root / subdir
            if d.is_dir():
                count = sum(1 for f in d.glob("*.md") if not f.name.startswith("_"))
                if count:
                    report_counts[rtype] = count
        if report_counts:
            result["report_counts"] = report_counts

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

    # ── Helpers ──

    @staticmethod
    def _paper_filename(paper) -> str:  # type: ignore[no-untyped-def]
        """Generate a readable filename for a paper (without .md extension)."""
        arxiv_id = getattr(paper, "source_paper_id", "") or ""
        arxiv_id = re.sub(r"[/\\:]", "_", arxiv_id).strip()
        title_slug = re.sub(r"[^\w\s-]", "", paper.title)[:80].strip().replace(" ", "_")
        if arxiv_id and arxiv_id != paper.id:
            return f"{arxiv_id}_{title_slug}"
        return title_slug

    def paper_wikilink(self, paper) -> str:  # type: ignore[no-untyped-def]
        """Return an Obsidian wikilink string for a paper: [[02-论文库/filename|title]]."""
        fname = self._paper_filename(paper)
        return f"[[02-论文库/{fname}|{paper.title}]]"
