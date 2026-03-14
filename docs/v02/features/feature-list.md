# Paper Agent v02 — Feature List

**Phase:** Phase 4 (特性拆解)
**Last Updated:** 2026-03-14

---

## 特性清单

| FEAT-ID | 名称 | 粒度 | Priority | 依赖 | Sprint |
|---------|------|------|----------|------|--------|
| FEAT-V2-01 | Workspace 基础设施 + Schema 迁移 | 细 | P0 | — | S1 |
| FEAT-V2-02 | 阅读状态管理 | 细 | P0 | FEAT-V2-01 | S1 |
| FEAT-V2-03 | 引用链追踪 | 细 | P0 | FEAT-V2-01 | S1 |
| FEAT-V2-04 | 论文笔记 | 粗 | P1 | FEAT-V2-01 | S2 |
| FEAT-V2-05 | 论文分组 | 粗 | P1 | FEAT-V2-01 | S2 |
| FEAT-V2-06 | 上下文恢复 + Skill/Rule 更新 | 粗 | P0 | FEAT-V2-01~05 | S2 |
| FEAT-V2-07 | 精确查找 + 下载 (paper_find_and_download) | 细 | P1 | — | S2 |
| FEAT-V2-08 | Workspace 仪表盘 (paper_workspace_status) | 细 | P1 | FEAT-V2-01 | S2 |

## 依赖 DAG

```
FEAT-V2-01 (Workspace 基础设施)
    ├── FEAT-V2-02 (阅读状态)
    ├── FEAT-V2-03 (引用链)
    ├── FEAT-V2-04 (笔记)
    └── FEAT-V2-05 (分组)
              │
              └── FEAT-V2-06 (上下文恢复)
```

## 迭代计划

### Sprint 1：核心基础 (FEAT-V2-01 + 02 + 03)

| 任务 | 说明 |
|------|------|
| Schema 迁移 | papers 表加 reading_status，新建 paper_notes、paper_groups、paper_group_items |
| WorkspaceManager | init、journal、reading-list 文件管理 |
| CitationService | S2 API 查询 + 论文入库 |
| MCP 工具 | paper_workspace_status、paper_reading_status、paper_reading_stats、paper_citations |
| CLI 集成 | `paper-agent setup cursor/claude-code` 自动创建 `.paper-agent/`，MCP 工具静默 auto-init |
| Workspace 文件生成 | journal 自动追加、reading-list 重建、citation-trace 生成 |

### Sprint 2：增强 + 集成 (FEAT-V2-04 + 05 + 06)

| 任务 | 说明 |
|------|------|
| 笔记工具 | paper_note_add、paper_note_show + notes/ 文件同步 |
| 分组工具 | paper_group_create/add/show/list + collections/ 文件同步 |
| 精确查找 | paper_find_and_download — 按标题多源查找 + 下载 PDF |
| 仪表盘 | paper_workspace_status — 生成 .paper-agent/README.md 人可读仪表盘 |
| 上下文恢复 | paper_workspace_context + SKILL.md / .mdc 更新 |

---

## 四可检验

### FEAT-V2-01: Workspace 基础设施

| 检验项 | 结论 |
|--------|------|
| 可感知 | ✅ 用户运行 `paper-agent setup` 后看到 .paper-agent/ 目录出现 |
| 可演示 | ✅ setup → 目录创建 → 文件可打开 → README.md 仪表盘 |
| 可端到端 | ✅ setup → MCP 工具自动 auto-init → 后续操作自动更新文件 |
| 可独立上线 | ✅ 不依赖其他 FEAT |

### FEAT-V2-02: 阅读状态管理

| 检验项 | 结论 |
|--------|------|
| 可感知 | ✅ 用户说"标记为待读" → reading-list.md 立即更新 |
| 可演示 | ✅ 标记状态 → 打开文件看到分组变化 |
| 可端到端 | ✅ 标记 → DB 更新 → 文件更新 → journal 记录 |
| 可独立上线 | ✅ 依赖 FEAT-V2-01 但 01 在同 Sprint |

### FEAT-V2-03: 引用链追踪

| 检验项 | 结论 |
|--------|------|
| 可感知 | ✅ 用户问"这篇引用了什么" → 获得引用列表 + 保存到文件 |
| 可演示 | ✅ 查引用 → 结果展示 → 打开 citation-traces/ 看到记录 |
| 可端到端 | ✅ 查询 → S2 API → 结果入库 → 文件保存 → journal |
| 可独立上线 | ✅ 同上 |
