# Paper Agent Plugin

这个目录包含 paper-agent 的 **IDE 插件分发物料**，用于通过 marketplace 分发给其他用户。

> **普通用户不需要手动操作这个目录。** 请使用 `paper-agent setup` 命令一键配置。

## 快速开始（推荐方式）

```bash
# Cursor 用户
paper-agent setup cursor

# Claude Code 用户
paper-agent setup claude-code
```

详见 [README - IDE Integration](../README.md#ide-integration)。

## 目录结构

```
plugin/
├── README.md                        ← 你在这里
├── install.sh                       ← 全局安装脚本（旧版，建议用 setup 命令代替）
└── claude-code/                     ← Claude Code plugin 物料
    ├── .claude-plugin/
    │   └── plugin.json              ← 插件清单
    ├── .mcp.json                    ← MCP 服务器配置模板
    ├── commands/                    ← Slash 命令定义
    │   ├── start-my-day.md          ← /start-my-day (one-call morning pipeline)
    │   ├── paper-search.md          ← /paper-search
    │   ├── paper-collect.md         ← /paper-collect
    │   ├── paper-analyze.md         ← /paper-analyze
    │   ├── paper-compare.md         ← /paper-compare
    │   ├── paper-survey.md          ← /paper-survey (quick-first)
    │   ├── paper-download.md        ← /paper-download
    │   ├── paper-setup.md           ← /paper-setup
    │   ├── paper-triage.md          ← /paper-triage (auto-classify)
    │   └── paper-insight.md         ← /paper-insight (trend analysis)
    └── skills/                      ← 工作流 Skills（AI 行为编排）
        ├── paper-intelligence/      ← 路由 Skill：根据意图分发到具体工作流
        │   └── SKILL.md
        ├── daily-reading/           ← 每日开工：上下文恢复→采集→推荐→标记
        │   ├── SKILL.md
        │   └── references/daily-digest-template.md
        ├── deep-dive/               ← 论文深度分析→笔记→状态→延伸
        │   ├── SKILL.md
        │   └── references/analysis-template.md
        ├── literature-survey/       ← 文献综述：关键词→搜索→筛选→综述→导出
        │   ├── SKILL.md
        │   └── references/survey-template.md
        ├── citation-explore/        ← 引用链探索：双向引用→递归追踪→整理
        │   ├── SKILL.md
        │   └── references/citation-map-template.md
        ├── paper-triage/            ← 论文筛选分流：批量评估→分流→标记
        │   ├── SKILL.md
        │   └── references/triage-template.md
        └── research-insight/        ← 研究趋势洞察：趋势分析→洞察报告
            ├── SKILL.md
            └── references/insight-template.md
```

## 工作流 Skills

Skills 是预编排的研究工作流，设计原则：**fork-only checkpoint**（只在分叉决策点暂停，结果前最多 2 轮确认），**quick-first**（默认轻量模式），**auto-track / opt-in export**（工作区操作自动执行，文件导出在 FORK 中确认），**表格 + 结论**（论文列表用表格，每个输出以「结论与建议」结尾）。

| Skill | 触发词 | 后端工具 | checkpoint 数 |
|-------|--------|---------|--------------|
| **daily-reading** | "start my day" | `paper_morning_brief` | 1 |
| **deep-dive** | "分析这篇" | `paper_show` + `paper_note_add(mark_as=)` | 2 |
| **literature-survey** | "综述"、"survey" | `paper_quick_scan` | 2 |
| **citation-explore** | "引用链" | `paper_citation_trace` | 1 |
| **paper-triage** | "筛一下" | `paper_auto_triage` | 2 |
| **research-insight** | "趋势" | `paper_quick_scan` + `paper_trend_data` | 1 |

v03 将多步 AI 链下沉为单次后端工具调用，总 checkpoint 从 ~23 降至 ~9。每个 workflow 结束时提供保存/导出选项。

## 命令速查

| 命令 | 功能 | 示例 |
|------|------|------|
| `/start-my-day` | 每日推荐（one-call: context+collect+digest+mark） | `/start-my-day` |
| `/paper-search` | 搜索论文 | `/paper-search GNN placement` |
| `/paper-collect` | 三源并行采集 | `/paper-collect` |
| `/paper-analyze` | 单篇深度分析 + 自动存笔记 | `/paper-analyze 2301.12345` |
| `/paper-compare` | 多篇对比 | `/paper-compare 2301.12345,2302.54321` |
| `/paper-survey` | 文献综述（quick-first） | `/paper-survey GNN for EDA` |
| `/paper-download` | 下载 PDF | `/paper-download 2301.12345` |
| `/paper-setup` | 初始化研究方向 | `/paper-setup` |
| `/paper-triage` | 批量筛选（auto-classify） | `/paper-triage` |
| `/paper-insight` | 趋势分析（trend data） | `/paper-insight GNN placement` |

## 输出格式

所有 workflow 遵循统一输出规范：

- **表格优先**: 论文列表一律使用表格（| # | 标题 | 评分 | 关键词 | 一句话 |），不使用 bullet list
- **结论必出**: 每个 workflow 输出在 FORK 选项之前包含「结论与建议」段，告诉研究员数据意味着什么
- **保存选项**: 每个 workflow 的最后一个 FORK 包含保存/导出选项

## MCP 工具一览

### 搜索与发现

| 工具 | 说明 |
|------|------|
| `paper_search(query, diverse)` | 本地 FTS5 搜索，`diverse=True` 自动扩展关键词（GNN → graph neural network） |
| `paper_search_batch(queries)` | 多方向批量搜索，一次调用搜 N 个方向，结果分组返回 |
| `paper_search_online(query, sources)` | 在线搜索 arXiv + Semantic Scholar（覆盖会议论文），`sources=["s2"]` 只搜会议 |

### 采集与管理

| 工具 | 说明 |
|------|------|
| `paper_collect(days)` | arXiv + DBLP + Semantic Scholar 三源并行采集，带实时进度日志 |
| `paper_survey_collect(keywords, venues)` | 回溯 N 年论文采集，用于文献综述 |

### 分析与对比

| 工具 | 说明 |
|------|------|
| `paper_show(paper_id)` | 单篇详情 |
| `paper_batch_show(paper_ids, detail)` | 批量查看（默认 compact 精简输出，`detail=True` 全量） |
| `paper_compare(paper_ids, aspects)` | 结构化对比数据 |

### Workspace（v02）

| 工具 | 说明 |
|------|------|
| `paper_workspace_status()` | 展示 Workspace 仪表盘 |
| `paper_workspace_context()` | 返回研究上下文 + `mode` 字段 ("workspace"/"lightweight") |
| `paper_reading_status(paper_ids, status)` | 设置阅读状态 |
| `paper_note_add(paper_id, content, mark_as)` | 添加笔记，可选同时标记状态 |
| `paper_group_add(name, paper_ids, create_if_missing)` | 向分组添加论文，可选自动建组 |
| `paper_citations(paper_id, direction)` | 单层引用查询 |

### 能力下沉工具（v03 新增）

| 工具 | 替代什么 | 说明 |
|------|---------|------|
| `paper_quick_scan(topic, limit)` | 3 步 AI 链 | 本地+在线搜索、去重、排序，一次调用 |
| `paper_auto_triage(paper_ids, top_n)` | AI 逐篇分析 | 基于已有评分自动三档分流 |
| `paper_citation_trace(paper_id, max_depth)` | 多轮递归 | 递归引用追踪，最多 3 层 |
| `paper_morning_brief(days)` | 3 次调用链 | context + collect + digest + auto-mark |
| `paper_trend_data(topic, years_back)` | AI 脑算 | 按年×方向统计论文数和趋势 |

### 导出与下载

| 工具 | 说明 |
|------|------|
| `paper_find_and_download(title)` | **精确查找**：按论文标题在 S2 + arXiv 多源查找 → 入库 → 下载 PDF |
| `paper_download(paper_ids)` | 批量下载 PDF（一次传多个 ID） |
| `paper_export(paper_ids, format)` | 导出 BibTeX / Markdown / JSON |

## Workspace 文件结构

运行 `paper-agent setup cursor` 或 `paper-agent setup claude-code` 后，在项目目录下生成：

```
.paper-agent/
├── research-journal.md         ← 研究日志（AI 自动记录每次操作）
├── reading-list.md             ← 阅读队列（按状态分组）
├── collections/                ← 论文分组
│   ├── _index.md               ← 分组索引
│   └── rl-placement.md         ← 每个分组一个文件
├── notes/                      ← 论文笔记
│   └── {paper_id}.md           ← 每篇论文一个文件
└── citation-traces/            ← 引用链追踪
    └── {trace_name}.md         ← 每次追踪一个文件
```

> 所有文件都是标准 markdown，可以直接在 IDE 中打开查看、编辑。
> 数据库是真相源，文件是"投影"——丢失可通过 MCP 工具自动重建。
> `.paper-agent/README.md` 是自动生成的仪表盘，随操作实时更新。

## 这个目录 vs `paper-agent setup`

| | `paper-agent setup` | `plugin/` 目录 |
|---|---|---|
| **用途** | 终端用户一键配置 IDE | 开发者维护插件分发物料 |
| **方式** | 自动写入配置文件 | 手动或通过 marketplace 安装 |
| **推荐** | ✅ 推荐所有用户使用 | 仅 marketplace 发布需要 |

## Claude Code Marketplace 发布

如需通过 marketplace 分发，可将此 repo 作为 marketplace 源：

```bash
# 其他用户在 Claude Code 中运行：
/plugin marketplace add linshaoxin-maker/paper_agent
/plugin install paper-agent@linshaoxin-maker-paper_agent
```

## Cursor Marketplace 发布

Cursor 插件需要 `.cursor-plugin/plugin.json` 格式，可在 [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish) 提交。
