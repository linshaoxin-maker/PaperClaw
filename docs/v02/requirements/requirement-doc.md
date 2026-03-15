# Paper Agent v02 — Requirement Doc

**Phase:** Phase 1 (需求定义)
**Status:** Draft
**Last Updated:** 2026-03-14
**Baseline:** `../v01/requirements/requirement-doc.md`

---

## 1. 背景与问题

### 1.1 v01 解决了什么
- 论文收集（arXiv + DBLP + S2 并行）
- 本地搜索（FTS5 + 关键词扩展 + 在线搜索）
- 单篇分析、多篇对比、文献综述、BibTeX 导出、PDF 下载

### 1.2 v01 遗留的问题

| 问题 | 影响 |
|------|------|
| **聊完即逝**：AI 不知道上次对话的上下文 | 研究员每次新会话都要重复说"我在做 XX 方向的 survey" |
| **数据不可见**：论文状态全在 SQLite 里 | 打开项目看不到"我读了什么、还差什么没读" |
| **无阅读管理**：收集了但不知道读了哪些 | 论文堆积，无法区分待读/已读/重要 |
| **无笔记系统**：分析结果在聊天记录里 | 换个会话窗口就找不到之前的分析了 |
| **无分组功能**：论文全平铺在一个库里 | 做不同方向的 survey 时无法分组管理 |
| **无引用追踪**：不能"顺藤摸瓜" | 发现一篇好论文后不能追踪引用链找更多 |

### 1.3 v02 目标

引入 **Workspace Layer**，让每次交互的结果持久化为人可读的 markdown 文件，同时作为 AI 的跨会话记忆。

---

## 2. 功能需求 (FR)

### 2.1 Workspace 基础设施

| FR-ID | 需求 | Priority | 依赖 |
|-------|------|----------|------|
| FR-W-01 | **Workspace 初始化**：`paper-agent setup cursor/claude-code` 创建 `.paper-agent/` 目录及模板文件；MCP 工具在 workspace 不存在时静默 auto-init | Must | — |
| FR-W-06 | **Workspace 仪表盘**：MCP 工具 `paper_workspace_status` 展示人可读摘要，自动更新 `.paper-agent/README.md` | Should | FR-W-01 |
| FR-W-02 | **研究日志自动记录**：每次 MCP 工具调用后，自动追加 journal 条目（时间 + 操作 + 结果摘要） | Must | FR-W-01 |
| FR-W-03 | **Journal 裁剪**：journal 超过 50 条时，自动将旧条目归档到 `research-journal-archive.md` | Should | FR-W-02 |
| FR-W-04 | **Workspace 重建**：从数据库重建所有 Workspace 文件（容灾） | Should | FR-W-01 |
| FR-W-05 | **Workspace 同步**：检测并修复 Workspace 文件与数据库的不一致 | Should | FR-W-01 |

### 2.2 阅读状态管理

| FR-ID | 需求 | Priority | 依赖 |
|-------|------|----------|------|
| FR-R-01 | **阅读状态字段**：Paper model 新增 `reading_status` 字段（`to_read` / `reading` / `read` / `important`） | Must | — |
| FR-R-02 | **状态更新工具**：MCP 工具 `paper_reading_status(paper_ids, status)` 更新论文状态 | Must | FR-R-01 |
| FR-R-03 | **Reading List 文件**：状态变更时自动更新 `reading-list.md`（按状态分组的表格） | Must | FR-W-01, FR-R-02 |
| FR-R-04 | **Reading List 归档**：已读论文超过 30 篇时，自动归档到 `reading-list-archive.md` | Should | FR-R-03 |
| FR-R-05 | **阅读统计**：MCP 工具 `paper_reading_stats` 返回各状态数量统计 | Could | FR-R-01 |

### 2.3 论文笔记

| FR-ID | 需求 | Priority | 依赖 |
|-------|------|----------|------|
| FR-N-01 | **笔记表**：数据库新增 `paper_notes` 表（`id`, `paper_id`, `content`, `source`, `created_at`, `updated_at`） | Must | — |
| FR-N-02 | **添加笔记工具**：MCP 工具 `paper_note_add(paper_id, content)` | Must | FR-N-01 |
| FR-N-03 | **查看笔记工具**：MCP 工具 `paper_note_show(paper_id)` 返回论文的所有笔记 | Must | FR-N-01 |
| FR-N-04 | **笔记文件同步**：添加笔记时自动创建/更新 `notes/{paper_id}.md` | Must | FR-W-01, FR-N-02 |
| FR-N-05 | **笔记搜索**：MCP 工具 `paper_note_search(query)` 在笔记内容中搜索 | Could | FR-N-01 |

### 2.4 论文分组

| FR-ID | 需求 | Priority | 依赖 |
|-------|------|----------|------|
| FR-C-01 | **分组表**：数据库新增 `paper_groups` 表（`id`, `name`, `description`, `created_at`）和 `paper_group_items` 关联表（注意：已有 `collections` 表是采集记录，避免冲突） | Must | — |
| FR-C-02 | **创建分组**：MCP 工具 `paper_group_create(name, description)` | Must | FR-C-01 |
| FR-C-03 | **添加到分组**：MCP 工具 `paper_group_add(name, paper_ids)` | Must | FR-C-01 |
| FR-C-04 | **查看分组**：MCP 工具 `paper_group_show(name)` 返回分组内论文列表 | Must | FR-C-01 |
| FR-C-05 | **列出所有分组**：MCP 工具 `paper_group_list()` | Must | FR-C-01 |
| FR-C-06 | **分组文件同步**：分组变更时自动更新 `collections/{name}.md` 和 `collections/_index.md` | Must | FR-W-01, FR-C-02 |
| FR-C-07 | **从分组移除**：MCP 工具 `paper_group_remove(name, paper_ids)` | Should | FR-C-01 |
| FR-C-08 | **删除分组**：MCP 工具 `paper_group_delete(name)` | Should | FR-C-01 |

### 2.5 引用链追踪

| FR-ID | 需求 | Priority | 依赖 |
|-------|------|----------|------|
| FR-CT-01 | **引用查询**：MCP 工具 `paper_citations(paper_id, direction, limit)` 查询论文的引用/被引用（通过 S2 API） | Must | — |
| FR-CT-02 | **引用结果保存**：查询结果中的论文自动保存到本地库 | Must | FR-CT-01 |
| FR-CT-03 | **引用链文件**：引用查询时自动创建/更新 `citation-traces/{topic}.md` | Must | FR-W-01, FR-CT-01 |
| FR-CT-04 | **引用深度控制**：支持指定追踪深度（默认 1 层，最大 2 层） | Should | FR-CT-01 |
| FR-CT-05 | **引用统计**：返回被引用次数、引用分布（按年份） | Could | FR-CT-01 |

### 2.6 精确查找 + 下载

| FR-ID | 需求 | Priority | 依赖 |
|-------|------|----------|------|
| FR-F-01 | **按标题查找**：MCP 工具 `paper_find_and_download(title)` 按标题在 Semantic Scholar + arXiv 多源查找论文 | Must | — |
| FR-F-02 | **自动入库**：找到的论文自动保存到本地库 | Must | FR-F-01 |
| FR-F-03 | **自动下载 PDF**：优先 arXiv PDF，其次 open-access URL | Must | FR-F-01 |
| FR-F-04 | **模糊标题匹配**：忽略大小写和标点进行标题匹配 | Should | FR-F-01 |

### 2.7 上下文恢复

| FR-ID | 需求 | Priority | 依赖 |
|-------|------|----------|------|
| FR-X-01 | **上下文摘要工具**：MCP 工具 `paper_workspace_context()` 返回 journal 最近 10 条 + reading-list 摘要 + 活跃集合 | Must | FR-W-01 |
| FR-X-02 | **AI 自动恢复**：SKILL.md 和命令定义中引导 AI 在会话开始时调用 `paper_workspace_context` | Must | FR-X-01 |

---

## 3. 用例规约 (UC)

### UC-V2-01: 初始化 Workspace

| 项目 | 内容 |
|------|------|
| 参与者 | 研究员 |
| 前置条件 | paper-agent 已安装，config 已初始化 |
| 主流程 | 1. 研究员运行 `paper-agent setup cursor/claude-code`  2. 系统创建 IDE 配置 + `.paper-agent/` 目录及模板文件  3. 系统确认创建成功 |
| 扩展流程 | 1a. 目录已存在 → 提示已初始化，跳过  1b. 未运行 setup，MCP 工具首次调用时静默 auto-init |
| 后置条件 | `.paper-agent/` 目录存在，含 journal、reading-list、collections/_index |

### UC-V2-02: 管理阅读状态

| 项目 | 内容 |
|------|------|
| 参与者 | 研究员 / AI 助手 |
| 前置条件 | 论文已在本地库中 |
| 主流程 | 1. 用户指定论文和目标状态  2. 系统更新数据库  3. 系统更新 reading-list.md  4. 系统追加 journal 条目 |
| 扩展流程 | 2a. 论文不存在 → 返回错误  4a. journal 超限 → 自动归档旧条目 |
| 后置条件 | 数据库、reading-list.md、journal 三处一致 |

### UC-V2-03: 添加论文笔记

| 项目 | 内容 |
|------|------|
| 参与者 | 研究员 / AI 助手 |
| 前置条件 | 论文已在本地库中 |
| 主流程 | 1. 用户提供 paper_id 和笔记内容  2. 系统保存到 notes 表  3. 系统创建/更新 `notes/{paper_id}.md`  4. 系统追加 journal 条目 |
| 扩展流程 | 3a. 笔记文件已存在 → 追加内容（不覆盖） |
| 后置条件 | 笔记在数据库和文件中均存在 |

### UC-V2-04: 管理论文集合

| 项目 | 内容 |
|------|------|
| 参与者 | 研究员 / AI 助手 |
| 前置条件 | Workspace 已初始化 |
| 主流程 | 1. 用户创建集合（名称 + 描述）  2. 系统创建数据库记录 + `collections/{name}.md`  3. 用户添加论文到集合  4. 系统更新关联表和文件 |
| 扩展流程 | 1a. 同名集合已存在 → 返回错误  3a. 批量添加 → 一次操作多篇 |
| 后置条件 | 集合在数据库、文件、_index.md 三处一致 |

### UC-V2-05: 追踪引用链

| 项目 | 内容 |
|------|------|
| 参与者 | 研究员 / AI 助手 |
| 前置条件 | 论文有 S2 可识别的 ID（DOI/arXiv ID/S2 Paper ID） |
| 主流程 | 1. 用户指定论文和方向（references/citations）  2. 系统调用 S2 API 获取引用/被引用列表  3. 系统将结果论文保存到本地库  4. 系统创建/更新 `citation-traces/{topic}.md`  5. 系统追加 journal 条目 |
| 扩展流程 | 2a. S2 API 不可用 → 降级提示  2b. 论文无 S2 ID → 尝试用标题搜索匹配 |
| 后置条件 | 引用关系已记录，新论文已入库 |

### UC-V2-06: 恢复上下文

| 项目 | 内容 |
|------|------|
| 参与者 | AI 助手 |
| 前置条件 | Workspace 已初始化 |
| 主流程 | 1. AI 在会话开始时调用 `paper_workspace_context`  2. 系统返回 journal 最近 10 条 + reading-list 摘要 + 活跃集合  3. AI 基于上下文主动提示用户 |
| 扩展流程 | 1a. Workspace 不存在 → 跳过，不影响其他功能 |
| 后置条件 | AI 了解用户最近的研究活动 |

---

## 4. 非功能需求 (NFR)

| NFR-ID | 类别 | 需求 | 量化指标 | 测量方法 |
|--------|------|------|---------|---------|
| NFR-V2-01 | 性能 | Workspace 文件更新延迟 | 工具响应时间 + 文件写入 < 500ms | 计时 |
| NFR-V2-02 | 性能 | 引用链查询响应时间 | 单层查询 < 5s（含 S2 API） | 计时 |
| NFR-V2-03 | 容量 | journal 文件大小 | < 100KB（约 50 条目） | 文件大小检查 |
| NFR-V2-04 | 容量 | reading-list 活跃论文数 | < 200 篇（已读自动归档） | 条目计数 |
| NFR-V2-05 | 可靠性 | Workspace ↔ 数据库一致性 | sync 后差异为 0 | 一致性校验 |
| NFR-V2-06 | 兼容性 | v01 → v02 升级 | 不丢失已有数据，Schema 向后兼容 | 升级测试 |
| NFR-V2-07 | 可用性 | Workspace 可选 | 不初始化 Workspace 不影响 v01 功能 | 功能测试 |

---

## 5. 体验指标 (UX)

| UX-ID | 类别 | 指标 | 目标值 | 测量方法 |
|-------|------|------|--------|---------|
| UX-V2-01 | 效率 | 标记阅读状态的操作步数 | ≤ 1 步（一句话完成） | 用户测试 |
| UX-V2-02 | 可见性 | 打开 IDE 到看到阅读进度 | ≤ 2 步（打开文件夹 + 打开文件） | 用户测试 |
| UX-V2-03 | 恢复力 | 新会话恢复上下文 | AI 主动提示"上次在做 XX" | 用户测试 |
| UX-V2-04 | 可学习性 | 理解 Workspace 概念 | 看到目录结构就明白 | 首次使用观察 |

---

## 6. 假设登记表

| ASM-ID | 假设 | 影响 | 验证方式 | 状态 |
|--------|------|------|---------|------|
| ASM-V2-01 | Semantic Scholar API 免费且稳定可用 | 引用链功能依赖 S2 | API 可用性测试 | 高置信（S2 API 公开免费） |
| ASM-V2-02 | 用户项目目录有写权限 | Workspace 文件创建 | 权限检查 | 高置信 |
| ASM-V2-03 | 用户愿意将 `.paper-agent/` 纳入 git | 跨设备同步 | 用户调研 | 中置信 |
| ASM-V2-04 | 研究员习惯在 IDE 中查看 markdown | Workspace 可见性价值 | 用户调研 | 高置信（IDE 用户群） |
| ASM-V2-05 | Journal 50 条目限制足够恢复上下文 | AI 上下文恢复质量 | 使用观察 | 中置信 |

---

## 7. 追溯矩阵种子

| Story | UC-ID | FR-IDs | NFR-IDs |
|-------|-------|--------|---------|
| 研究员想看到自己的阅读进度 | UC-V2-02 | FR-R-01~05 | NFR-V2-01, UX-V2-02 |
| 研究员想记录读论文的想法 | UC-V2-03 | FR-N-01~05 | NFR-V2-01 |
| 研究员想把论文分组管理 | UC-V2-04 | FR-C-01~08 | NFR-V2-01 |
| 研究员想追踪引用链发现更多论文 | UC-V2-05 | FR-CT-01~05 | NFR-V2-02 |
| AI 想知道用户上次在干什么 | UC-V2-06 | FR-X-01~02, FR-W-02~03 | NFR-V2-03, UX-V2-03 |
| 研究员想从零开始初始化工作台 | UC-V2-01 | FR-W-01~06 | NFR-V2-06~07 |
| 研究员给一个论文标题让 AI 找到并下载 | UC-V2-07 | FR-F-01~04 | NFR-V2-02 |
