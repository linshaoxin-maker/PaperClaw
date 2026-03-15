# Paper Agent v02 — Technical Design Doc

**Phase:** Phase 3 (技术设计)
**Status:** Draft
**Last Updated:** 2026-03-14

---

## 1. 组件设计

### 1.1 新增组件

```
paper_agent/
├── services/
│   ├── workspace_manager.py    ← NEW: Workspace 文件管理
│   └── citation_service.py     ← NEW: S2 引用链查询
├── domain/models/
│   └── paper.py                ← MOD: 新增 reading_status 字段
├── infra/storage/
│   └── sqlite_storage.py       ← MOD: 新增表 + 查询方法
├── cli/commands/
│   └── setup.py                ← MOD: 新增 workspace init
└── mcp/
    └── tools.py                ← MOD: 新增 12 个 MCP 工具
```

### 1.2 组件依赖

```
MCP Tools ─→ WorkspaceManager ─→ SQLiteStorage
    │              │
    │              └─→ 文件系统 (.paper-agent/)
    │
    ├─→ CitationService ─→ S2 API
    │        │
    │        └─→ SQLiteStorage (保存新论文)
    │
    └─→ SQLiteStorage (直接查询)
```

### 1.3 WorkspaceManager 职责

```python
class WorkspaceManager:
    """管理 .paper-agent/ 目录下所有 Workspace 文件。"""

    def __init__(self, workspace_dir: Path, storage: SQLiteStorage | None = None):
        ...

    # --- 初始化 ---
    def init(self) -> dict                           # 创建目录+模板
    def is_initialized(self) -> bool                 # 检查是否已初始化
    def ensure_initialized(self) -> None             # MCP 工具静默自动初始化

    # --- Dashboard ---
    def rebuild_dashboard(self) -> None               # 重新生成 .paper-agent/README.md 仪表盘

    # --- Journal ---
    def append_journal(self, summary: str, details: dict) -> None
    def trim_journal(self, max_entries: int = 50) -> None

    # --- Reading List ---
    def rebuild_reading_list(self) -> None            # 从 DB 重新生成文件
    def archive_read_papers(self, max_read: int = 30) -> None

    # --- Notes ---
    def sync_note_file(self, paper_id: str) -> None   # 从 DB 生成 notes/{id}.md

    # --- Collections ---
    def sync_collection_file(self, name: str) -> None # 从 DB 生成 collections/{name}.md
    def rebuild_collection_index(self) -> None        # 重建 _index.md

    # --- Citation Traces ---
    def update_citation_trace(self, trace_name: str, paper_id: str,
                              refs: list, cites: list) -> None

    # --- Context ---
    def get_context(self) -> dict                     # 返回上下文摘要
    def rebuild_all(self) -> None                     # 容灾：从 DB 完全重建
```

### 1.4 CitationService 职责

```python
class CitationService:
    """通过 Semantic Scholar API 查询论文引用关系。"""

    S2_API = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, storage: SQLiteStorage):
        ...

    def get_citations(self, paper_id: str, direction: str = "both",
                      limit: int = 20) -> dict:
        """查询论文的引用/被引用列表，新论文自动入库。"""
        ...

    def _resolve_s2_id(self, paper_id: str) -> str | None:
        """从本地论文记录中提取 S2 Paper ID，或通过 API 查找。"""
        ...
```

---

## 2. Schema 变更

### 2.1 papers 表扩展

```sql
-- v02 迁移：添加阅读状态
ALTER TABLE papers ADD COLUMN reading_status TEXT DEFAULT NULL;
ALTER TABLE papers ADD COLUMN reading_status_at TEXT DEFAULT NULL;
```

### 2.2 新表：paper_notes

```sql
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
```

### 2.3 新表：paper_groups + paper_group_items

> 注意：已有的 `collections` 表是 **采集记录** 表，此处使用 `paper_groups` 避免冲突。

```sql
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
```

### 2.4 迁移策略

- 使用 `_SCHEMA_VERSION = 2` 标记
- 启动时检查版本，自动执行 ALTER/CREATE
- 向后兼容：v01 数据库在 v02 启动时自动升级

---

## 3. MCP 工具契约

### 3.1 新增工具清单

| 工具 | 输入 | 输出 | 副作用 |
|------|------|------|--------|
| `paper_workspace_status` | — | `{dashboard, stats, groups}` | 更新 .paper-agent/README.md 仪表盘 |
| `paper_workspace_context` | — | `{journal, reading, collections}` | 无（静默自动初始化 workspace） |
| `paper_reading_status` | `paper_ids[], status` | `{updated, summary}` | 更新 DB + reading-list.md + journal |
| `paper_reading_stats` | — | `{to_read, reading, read, important}` | 无 |
| `paper_note_add` | `paper_id, content, source?` | `{note_id, file}` | 插入 DB + notes/{id}.md + journal |
| `paper_note_show` | `paper_id` | `{notes[]}` | 无 |
| `paper_group_create` | `name, description?` | `{id, file}` | 插入 DB + collections/{name}.md + journal |
| `paper_group_add` | `name, paper_ids[]` | `{added, total}` | 插入 DB + 更新文件 + journal |
| `paper_group_show` | `name` | `{papers[], description}` | 无 |
| `paper_group_list` | — | `{groups[]}` | 无 |
| `paper_citations` | `paper_id, direction?, limit?, trace_name?` | `{refs[], cites[]}` | S2 API + 入库 + citation-traces/ + journal |
| `paper_find_and_download` | `title, output_dir?` | `{paper, download}` | S2/arXiv 多源查找 → 入库 → 下载 PDF |

> **Workspace 初始化方式**：由 `paper-agent setup cursor/claude-code` CLI 命令创建 `.paper-agent/`。
> MCP 工具在 workspace 不存在时静默自动初始化（`_ensure_workspace()`）。

---

## 4. 变更影响分析

| 受影响模块 | 变更类型 | 影响说明 |
|-----------|---------|---------|
| `sqlite_storage.py` | 修改 | 新增 Schema 迁移 + 6 个新查询方法 |
| `paper.py` | 修改 | 新增 `reading_status` 和 `reading_status_at` 字段 |
| `context.py` | 修改 | 注入 WorkspaceManager 和 CitationService |
| `tools.py` | 修改 | 新增 12 个 MCP 工具（含 paper_find_and_download） |
| `server.py` | 修改 | 更新 _DESCRIPTION |
| `setup.py` | 修改 | setup cursor/claude-code 自动创建 .paper-agent/ |
| 已有 MCP 工具 | 不变 | 全部向后兼容 |
