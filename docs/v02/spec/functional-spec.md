# Paper Agent v02 — Functional Spec

**Phase:** Phase 2 (功能规格)
**Status:** Draft
**Last Updated:** 2026-03-13

---

## 1. Workspace 初始化

### 1.1 MCP Tool: `paper_workspace_init`

**触发**：用户首次使用 workspace 相关功能，或显式调用
**输入**：`workspace_dir: str | None`（默认当前工作目录下 `.paper-agent/`）

**行为**：
1. 检查 `{workspace_dir}` 是否已存在
   - 已存在且完整 → 返回 `{"status": "already_initialized", "path": "..."}`
   - 已存在但不完整 → 补全缺失文件
   - 不存在 → 创建目录结构
2. 创建以下文件/目录：
   ```
   .paper-agent/
   ├── research-journal.md     ← 空模板
   ├── reading-list.md         ← 空模板
   ├── collections/
   │   └── _index.md           ← 空索引
   ├── notes/                  ← 空目录
   └── citation-traces/        ← 空目录
   ```
3. 返回 `{"status": "initialized", "path": "...", "files_created": [...]}`

**异常**：
- 无写权限 → `{"status": "error", "message": "Permission denied"}`

---

## 2. 研究日志 (Research Journal)

### 2.1 自动记录机制

**触发**：任何 MCP 工具调用完成后
**行为**：
1. 构建条目：`### HH:MM — {操作摘要}\n- {关键信息}\n`
2. 检查 journal 文件是否存在（不存在则跳过，不阻塞主操作）
3. 读取 journal 文件，在当天日期标题下追加条目
4. 如果当天日期标题不存在，在文件开头（header 之后）插入日期标题
5. 统计条目总数，超过 50 条触发归档

**条目格式**：
```markdown
### 09:30 — 搜索 RL placement 论文
- 查询: "reinforcement learning chip placement"
- 结果: 本地 12 篇, 在线 25 篇
- 下一步: 选 15 篇做 survey
```

**操作→摘要映射**：

| MCP Tool | Journal 摘要格式 |
|----------|-----------------|
| `paper_collect` | 每日收集: {new} 篇新增, {dup} 篇重复 |
| `paper_search` | 搜索: "{query}" → {count} 篇结果 |
| `paper_search_online` | 在线搜索: "{query}" → arXiv {n1} + S2 {n2} 篇 |
| `paper_reading_status` | 标记{status}: {paper_titles} |
| `paper_note_add` | 笔记: {paper_title} — {content_preview} |
| `paper_collection_create` | 创建集合: {name} |
| `paper_collection_add` | 添加到 {collection}: {count} 篇 |
| `paper_citations` | 引用链: {paper_title} → {direction} {count} 篇 |
| `paper_compare` | 对比: {count} 篇论文 |
| `paper_download` | 下载: {count} 篇 PDF |

### 2.2 Journal 归档

**触发**：条目总数 > 50
**行为**：
1. 保留最近 30 条，将最早的 20+ 条移到 `research-journal-archive.md`
2. archive 文件按月份分段，追加模式
3. 更新 journal 文件 header 中的 `Entries` 计数

---

## 3. 阅读状态管理

### 3.1 Schema 变更

```sql
ALTER TABLE papers ADD COLUMN reading_status TEXT DEFAULT NULL;
-- 值: NULL (未标记) | 'to_read' | 'reading' | 'read' | 'important'

ALTER TABLE papers ADD COLUMN reading_status_updated_at TEXT DEFAULT NULL;
```

### 3.2 MCP Tool: `paper_reading_status`

**输入**：
- `paper_ids: list[str]` — 论文 ID 列表
- `status: str` — 目标状态 (`to_read` | `reading` | `read` | `important` | `clear`)

**行为**：
1. 验证 paper_ids 都存在
2. 更新数据库 `reading_status` 和 `reading_status_updated_at`
3. 重新生成 `reading-list.md`：
   - 按状态分组：🔴 To Read → 🟡 Reading → 🟢 Read → ⭐ Important
   - 每组内按更新时间倒序
   - Read 组超过 30 篇时，最早的移到 archive
4. 追加 journal 条目
5. 返回 `{"status": "ok", "updated": N, "reading_list_summary": {...}}`

**`clear` 状态**：移除阅读状态标记（回到 NULL），同时从 reading-list.md 移除

### 3.3 MCP Tool: `paper_reading_stats`

**输入**：无
**返回**：
```json
{
  "to_read": 5,
  "reading": 1,
  "read": 12,
  "important": 3,
  "total_tracked": 21,
  "recent_reads": [{"title": "...", "finished": "2026-03-14"}]
}
```

### 3.4 reading-list.md 格式规格

```markdown
# Reading List

> Last updated: {timestamp}
> Stats: {to_read} to-read · {reading} reading · {read} read · {important} important

## 🔴 To Read ({count})

| Paper | Score | Added | Source |
|-------|-------|-------|--------|
| [{title}](paper://{id}) | {score} | {date} | {source} |

## 🟡 Reading ({count})

| Paper | Started | Notes |
|-------|---------|-------|
| [{title}](paper://{id}) | {date} | {brief} |

## ⭐ Important ({count})

| Paper | Rating | Why |
|-------|--------|-----|
| [{title}](paper://{id}) | {score} | {reason} |

## 🟢 Recently Read ({count}, max 30)

| Paper | Finished | Notes |
|-------|----------|-------|
| [{title}](paper://{id}) | {date} | [笔记](notes/{id}.md) |
```

---

## 4. 论文笔记

### 4.1 Schema

```sql
CREATE TABLE notes (
    id TEXT PRIMARY KEY,
    paper_id TEXT NOT NULL REFERENCES papers(id),
    content TEXT NOT NULL,
    source TEXT DEFAULT 'user',  -- 'user' | 'ai_analysis'
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX idx_notes_paper ON notes(paper_id);
```

### 4.2 MCP Tool: `paper_note_add`

**输入**：
- `paper_id: str`
- `content: str`
- `source: str = "user"` — `user`（用户笔记）或 `ai_analysis`（AI 分析结果）

**行为**：
1. 验证 paper_id 存在
2. 插入 notes 表
3. 创建/更新 `notes/{paper_id}.md`：
   - 文件头：论文标题 + 元数据
   - 按时间倒序排列笔记条目
   - 标注来源（👤 用户 / 🤖 AI）
4. 追加 journal 条目
5. 返回 `{"status": "ok", "note_id": "...", "file": "notes/{paper_id}.md"}`

### 4.3 notes/{paper_id}.md 格式规格

```markdown
# Notes: {paper_title}

> Paper ID: {id}
> Authors: {authors}
> Published: {date}
> Score: {score}
> Status: {reading_status}

---

## 2026-03-14 09:30 (👤 User)

方法很不错但只在小规模上验证了。PPO + Graph embedding 的组合值得参考。

## 2026-03-14 09:25 (🤖 AI Analysis)

### 核心方法
...

### 实验结果
...
```

---

## 5. 论文集合

### 5.1 Schema

```sql
CREATE TABLE collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE collection_papers (
    collection_id TEXT NOT NULL REFERENCES collections(id),
    paper_id TEXT NOT NULL REFERENCES papers(id),
    added_at TEXT NOT NULL,
    note TEXT DEFAULT '',
    PRIMARY KEY (collection_id, paper_id)
);
```

### 5.2 MCP Tool: `paper_collection_create`

**输入**：`name: str`, `description: str = ""`
**行为**：
1. 验证名称不重复
2. 插入 collections 表
3. 创建 `collections/{name}.md`（空模板 + 描述）
4. 更新 `collections/_index.md`
5. 追加 journal 条目

### 5.3 MCP Tool: `paper_collection_add`

**输入**：`collection_name: str`, `paper_ids: list[str]`
**行为**：
1. 验证集合和论文都存在
2. 批量插入 collection_papers（已存在的跳过）
3. 重新生成 `collections/{name}.md`
4. 追加 journal 条目
5. 返回 `{"status": "ok", "added": N, "skipped": M, "total": T}`

### 5.4 collections/{name}.md 格式规格

```markdown
# Collection: {display_name}

> Purpose: {description}
> Created: {date}
> Papers: {count}

| # | Paper | Year | Authors | Score |
|---|-------|------|---------|-------|
| 1 | [{title}](paper://{id}) | {year} | {authors_short} | {score} |

## Notes

{user_notes_if_any}
```

---

## 6. 引用链追踪

### 6.1 MCP Tool: `paper_citations`

**输入**：
- `paper_id: str`
- `direction: str = "both"` — `references`（被引论文）/ `citations`（引用了它的论文）/ `both`
- `limit: int = 20`
- `trace_name: str | None` — 关联的引用链名称（用于保存到 citation-traces/）

**行为**：
1. 从本地库获取论文的 S2 Paper ID（如无，用标题/arXiv ID 查 S2 API 匹配）
2. 调用 S2 API `/paper/{s2_id}/references` 和/或 `/paper/{s2_id}/citations`
3. 解析结果，按引用次数/相关度排序
4. 将结果论文保存到本地库（如不存在）
5. 如指定 `trace_name`，更新 `citation-traces/{trace_name}.md`
6. 追加 journal 条目
7. 返回结构化结果

**返回格式**：
```json
{
  "status": "ok",
  "paper": {"id": "...", "title": "..."},
  "references": [{"id": "...", "title": "...", "year": 2024, "citation_count": 150}],
  "citations": [{"id": "...", "title": "...", "year": 2026, "citation_count": 5}],
  "trace_file": "citation-traces/rl-placement.md"
}
```

### 6.2 citation-traces/{name}.md 格式规格

```markdown
# Citation Trace: {topic_name}

> Created: {date}
> Last updated: {date}
> Root papers: {count}

## {paper_title} ({year})

### References (cited by this paper)
| # | Paper | Year | Citations | In Library |
|---|-------|------|-----------|------------|
| 1 | [{title}](paper://{id}) | {year} | {count} | ✅/❌ |

### Citations (papers that cite this)
| # | Paper | Year | Citations | In Library |
|---|-------|------|-----------|------------|
| 1 | [{title}](paper://{id}) | {year} | {count} | ✅/❌ |
```

---

## 7. 上下文恢复

### 7.1 MCP Tool: `paper_workspace_context`

**输入**：无
**行为**：
1. 检查 `.paper-agent/` 是否存在（不存在 → 返回空上下文）
2. 读取 journal 最近 10 条
3. 读取 reading-list 摘要（各状态数量 + to_read 和 reading 的具体论文）
4. 读取 collections/_index.md 获取活跃集合列表
5. 组装上下文摘要

**返回格式**：
```json
{
  "status": "ok",
  "has_workspace": true,
  "journal_recent": [
    {"time": "2026-03-14 09:30", "summary": "搜索 RL placement 论文"},
    {"time": "2026-03-14 09:15", "summary": "每日收集: 47 篇新增"}
  ],
  "reading_list": {
    "to_read": 5,
    "reading": 1,
    "reading_papers": [{"id": "...", "title": "..."}],
    "read": 12,
    "important": 3
  },
  "collections": [
    {"name": "rl-placement", "paper_count": 15, "last_updated": "2026-03-14"}
  ],
  "suggestion": "你上次在做 RL Placement 方向的 survey，集合里有 15 篇论文。要继续吗？"
}
```

---

## 8. 文件写入规范（跨功能）

### 8.1 原则

1. **数据库是真相源**：Workspace 文件从数据库生成，不是反过来
2. **幂等生成**：文件内容从数据库重新生成，而非追加。避免不一致
3. **写入不阻塞**：文件写入失败不影响 MCP 工具返回。错误记录到日志
4. **UTF-8 编码**：所有文件使用 UTF-8，无 BOM

### 8.2 Journal 特殊处理

Journal 是唯一的"追加模式"文件（其他文件都是重新生成）：
- 条目按时间追加
- 归档时批量移除旧条目
- 这保证了 journal 的自然叙事流

### 8.3 文件锁

多个工具可能并发写同一文件。采用简单的文件锁：
- 写入前创建 `{file}.lock`
- 写入完成后删除 `.lock`
- 检测到 `.lock` 存在且超过 10s → 强制删除（认为上次写入中断）
