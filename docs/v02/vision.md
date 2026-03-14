# Paper Agent v02 — Vision

**Phase:** Phase 0 (想法澄清)
**Status:** Draft
**Last Updated:** 2026-03-13
**Baseline:** `../v01/idea-brief.md`

---

## 1. 愿景陈述

> Paper Agent v02 引入 **Workspace Layer**——一组人可读、AI 可读的 markdown 文件，作为研究员和 AI 助手之间的"共享工作记忆"。研究员打开项目目录就能看到阅读队列、论文笔记、分组集合、引用链探索记录；AI 在每次会话开始时读取这些文件，无需用户重复说明上下文。数据库管数据，Workspace 管记忆。

### 1.1 v01 → v02 的核心跃迁

| | v01 (已实现) | v02 (本版本) |
|---|---|---|
| **数据存储** | SQLite（人不可见） | SQLite + Workspace markdown（人可见） |
| **跨会话记忆** | 无 | `research-journal.md` = AI 的记忆 |
| **用户看全貌** | 必须问 AI | 打开文件夹就看到 |
| **论文状态** | 无状态 | to-read → reading → read → important |
| **笔记** | 无 | 每篇论文一个 `notes/{id}.md` |
| **分组** | 无 | `collections/{name}.md` |
| **引用链** | 无 | `citation-traces/{topic}.md` |
| **交互模式** | 聊天即逝 | 文件 = 持久化的交互结果 |

---

## 2. 架构概念：Workspace Layer

### 2.1 三层架构

```
┌─ 交互层 (Claude Code / Cursor) ──────────────────────────┐
│  自然语言 / slash 命令 → AI 理解 → 调用工具 → 格式化呈现  │
└──────────────────────────┬───────────────────────────────┘
                           │ MCP 协议 + 文件读写
┌─ Workspace Layer (NEW) ──┴──────────────────────────────┐
│  .paper-agent/                                            │
│  ├── research-journal.md    ← 研究日志（AI 的记忆）       │
│  ├── reading-list.md        ← 阅读队列（状态管理）        │
│  ├── collections/           ← 论文分组                    │
│  ├── notes/                 ← 论文笔记                    │
│  └── citation-traces/       ← 引用链探索                  │
│                                                           │
│  特性：人可读 · AI 可读 · 自动更新 · 有裁剪策略            │
└──────────────────────────┬──────────────────────────────┘
                           │ MCP 协议
┌─ 数据层 (paper-agent-mcp) ──────────────────────────────┐
│  SQLite 论文库 · LLM 评分 · arXiv/DBLP/S2 采集 · 配置    │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Workspace 目录结构

```
{project-root}/
└── .paper-agent/                      ← Workspace 根目录
    ├── research-journal.md            ← 研究日志（最近 50 条，老的自动归档）
    ├── reading-list.md                ← 阅读队列（按状态分组）
    ├── reading-list-archive.md        ← 已读归档（定期从 reading-list 迁入）
    ├── collections/                   ← 论文分组
    │   ├── _index.md                  ← 所有集合的索引
    │   ├── rl-placement.md            ← 一个集合 = 一个文件
    │   └── memory-survey.md
    ├── notes/                         ← 论文笔记
    │   ├── 2603.04567.md              ← 一篇论文 = 一个笔记
    │   └── 2501.05678.md
    └── citation-traces/               ← 引用链探索
        ├── rl-placement.md            ← 一个方向 = 一个引用链
        └── gnn-eda.md
```

### 2.3 Workspace 设计原则

| 原则 | 说明 |
|------|------|
| **人可读优先** | 所有文件都是标准 markdown，用任何编辑器/IDE 都能打开 |
| **AI 可读** | 文件格式结构化（frontmatter + 表格），AI 可解析提取信息 |
| **自动维护** | MCP 工具在操作时自动更新对应文件（搜索→更新 journal，标记已读→更新 reading-list） |
| **有限增长** | journal 保留最近 50 条；reading-list 已读部分定期归档；不会无限膨胀 |
| **数据库是真相源** | Workspace 文件是数据库的"投影"，不是数据源。丢了 workspace 可以从 DB 重建 |
| **幂等更新** | 重复写入同一内容不会产生重复条目 |

### 2.4 Workspace 文件格式示例

**research-journal.md**：
```markdown
# Research Journal

> Last updated: 2026-03-14 09:30
> Entries: 12 (max 50, auto-archived)

## 2026-03-14

### 09:30 — 搜索 RL placement 论文
- 查询: "reinforcement learning chip placement"
- 结果: 本地 12 篇, 在线补充 25 篇
- 下一步: 选 15 篇做 survey

### 09:15 — 每日收集
- 新增: 47 篇 (arXiv 28 + DBLP 12 + S2 7)
- 高置信推荐: 5 篇
- 标记待读: #3 RL-Placer, #5 GNN-Routing

## 2026-03-13
...
```

**reading-list.md**：
```markdown
# Reading List

> Last updated: 2026-03-14 09:30

## 🔴 To Read (5)

| Paper | Score | Added | Source |
|-------|-------|-------|--------|
| [RL-Placer: Deep RL for...](paper://2603.04567) | 9.2 | 03-14 | digest |
| [GNN-Driven Routing...](paper://2603.04321) | 8.7 | 03-14 | digest |
| ... | | | |

## 🟡 Reading (1)

| Paper | Started | Notes |
|-------|---------|-------|
| [Transformer-Placement](paper://2603.04567) | 03-14 | 看到 Section 3 |

## 🟢 Read (3)

| Paper | Finished | Rating | Notes |
|-------|----------|--------|-------|
| [MaskPlace](paper://2401.09012) | 03-13 | ⭐⭐⭐ | [笔记](notes/2401.09012.md) |
| ... | | | |
```

**collections/rl-placement.md**：
```markdown
# Collection: RL for Chip Placement

> Purpose: Survey on RL-based placement methods
> Created: 2026-03-14
> Papers: 15

| # | Paper | Year | Method | Key Result |
|---|-------|------|--------|------------|
| 1 | [RL-Placer](paper://2603.04567) | 2026 | PPO + Graph | HPWL -15.3% |
| 2 | [ChipFormer](paper://2501.05678) | 2025 | SAC + Transformer | HPWL -11.8% |
| ... | | | | |

## Notes
- 这些论文共同的趋势: 从 DQN → PPO/SAC, 状态表示从 CNN → GNN/Transformer
- 缺少的方向: timing-aware placement
```

---

## 3. 范围边界表

| 类别 | 内容 |
|------|------|
| **In Scope (v02)** | Workspace Layer（journal + reading-list + collections + notes + citation-traces）· 阅读状态管理 · 论文笔记 · 论文分组 · 引用链追踪（S2 API）· Workspace 生命周期管理（裁剪/归档）· MCP 工具扩展 · CLI 命令扩展 |
| **Out of Scope** | PDF 全文深度解析 · 论文 Q&A · 趋势可视化图表 · Web UI · 团队协作 · Related Work 自动生成 |
| **Future (v03+)** | Paper Q&A（PDF 解析 + LLM）· 趋势分析与可视化 · Related Work 生成 · arXiv 版本更新追踪 · 团队共享 Workspace |

## 4. 干系人地图

| 角色 | 关注点 | 参与阶段 | 沟通频率 |
|------|--------|---------|---------|
| Individual AI Researcher (主要) | 跨会话记忆、阅读进度可视化、笔记管理 | 需求→验收 | 每日使用 |
| PhD Student / Early Researcher | 文献分组、引用链探索、survey 工作台 | 需求→验收 | 每日使用 |
| AI Assistant (Claude Code / Cursor) | 读取 Workspace 恢复上下文、自动更新文件 | 设计→集成 | 每次会话 |
| 开发者 (self) | Workspace 与数据库一致性、文件格式稳定性 | 全程 | 持续 |

## 5. 开放问题清单

| # | 问题 | 影响 | 状态 |
|---|------|------|------|
| OQ-V2-001 | Workspace 根目录用 `.paper-agent/` 还是 `paper-workspace/`？ | 用户可见性 vs 隐藏文件约定 | 待确认 |
| OQ-V2-002 | journal 条目超过 50 条时，归档到哪里？独立文件 or 删除？ | 磁盘空间 vs 历史追溯 | 待确认 |
| OQ-V2-003 | reading-list 的状态更新是 MCP 工具驱动还是用户手动编辑文件？ | 工具设计 | 倾向工具驱动，但支持手动编辑 |
| OQ-V2-004 | citation-traces 的引用链深度限制多少层？ | S2 API 调用量 | 待确认（建议 2 层） |
| OQ-V2-005 | Workspace 文件是否纳入 git？ | 版本管理 vs 个人偏好 | 建议默认纳入 |
| OQ-V2-006 | 笔记文件是否支持用户直接在 IDE 编辑后被 AI 识别？ | 双向同步复杂度 | 待确认 |

---

## 6. v02 功能清单（概览）

### P0 — 核心

| 功能 | 说明 | 关联 Workspace 文件 |
|------|------|-------------------|
| **Workspace 初始化** | `paper-agent workspace init` 创建 `.paper-agent/` 目录和模板文件 | 全部 |
| **研究日志** | 每次工具调用自动追加 journal 条目 | `research-journal.md` |
| **阅读状态管理** | Paper model 加 `status` 字段 + MCP 工具 `paper_reading_status` | `reading-list.md` |
| **引用链追踪** | S2 API `citations` + `references` + MCP 工具 `paper_citations` | `citation-traces/` |

### P1 — 增强

| 功能 | 说明 | 关联 Workspace 文件 |
|------|------|-------------------|
| **论文笔记** | MCP 工具 `paper_note_add` / `paper_note_show` + notes 表 | `notes/` |
| **论文分组** | MCP 工具 `paper_collection_create` / `_add` / `_show` + collections 表 | `collections/` |

### P2 — 优化

| 功能 | 说明 | 关联 Workspace 文件 |
|------|------|-------------------|
| **Workspace 裁剪** | journal 自动归档、reading-list 已读归档 | 生命周期管理 |
| **Workspace 重建** | 从数据库重建 Workspace 文件（容灾） | 全部 |
| **上下文恢复** | AI 会话开始时读取 journal + reading-list 恢复上下文 | journal + reading-list |

---

## 7. 与 v01 的关系

- v02 是 v01 的**增量扩展**，不修改 v01 的核心架构
- 数据库 Schema 新增字段和表，向后兼容
- 所有 v01 MCP 工具保持不变，新增 Workspace 相关工具
- Workspace Layer 是可选的——不初始化 workspace 不影响 v01 功能
