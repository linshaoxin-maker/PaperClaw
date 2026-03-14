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
    │   ├── start-my-day.md          ← /start-my-day
    │   ├── paper-search.md          ← /paper-search
    │   ├── paper-collect.md         ← /paper-collect
    │   ├── paper-analyze.md         ← /paper-analyze
    │   ├── paper-compare.md         ← /paper-compare
    │   ├── paper-survey.md          ← /paper-survey
    │   ├── paper-download.md        ← /paper-download
    │   └── paper-setup.md           ← /paper-setup
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

Skills 是预编排的研究工作流，AI 会在关键节点与用户交互，最终产出结构化交付件。

| Skill | 触发词 | 交付件 | 默认路径 |
|-------|--------|--------|---------|
| **daily-reading** | "每日开工"、"start my day" | 每日阅读摘要 | `daily/{date}.md` |
| **deep-dive** | "分析这篇"、"展开讲讲" | 论文分析笔记 | `.paper-agent/notes/{id}.md` |
| **literature-survey** | "综述"、"survey" | 综述报告 + BibTeX | `survey/{topic}.md` |
| **citation-explore** | "引用链"、"citations" | 引用图谱报告 | `.paper-agent/citation-traces/{name}.md` |
| **paper-triage** | "帮我筛一下"、"哪些值得读" | 筛选决策表 | `triage/{topic}-{date}.md` |
| **research-insight** | "趋势"、"洞察" | 趋势洞察报告 | `insight/{topic}-{date}.md` |

每个 Skill 都有：交互检查点（🗣️ 必须问用户）、交付件模板、Skill 间跳转。

## 命令速查

| 命令 | 功能 | 示例 |
|------|------|------|
| `/start-my-day` | 每日论文推荐 | `/start-my-day` |
| `/paper-search` | 搜索论文（本地 + 在线，支持关键词扩展） | `/paper-search GNN placement` |
| `/paper-collect` | 从 arXiv + DBLP + Semantic Scholar 并行采集 | `/paper-collect` |
| `/paper-analyze` | 单篇论文深度分析 | `/paper-analyze 2301.12345` |
| `/paper-compare` | 多篇论文对比表格 | `/paper-compare 2301.12345,2302.54321` |
| `/paper-survey` | 生成文献综述（支持多方向批量搜索） | `/paper-survey GNN for EDA` |
| `/paper-download` | 批量下载 PDF 文件 | `/paper-download 2301.12345,2302.54321` |
| `/paper-setup` | 初始化研究方向 | `/paper-setup` |

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

### Workspace（v02 新增）

| 工具 | 说明 |
|------|------|
| `paper_workspace_init()` | 初始化 `.paper-agent/` 目录（journal、reading-list、notes、collections、citation-traces） |
| `paper_workspace_context()` | 返回研究上下文摘要，用于新会话恢复（AI 读此知道你之前在干什么） |
| `paper_reading_status(paper_ids, status)` | 设置阅读状态：`to_read` / `reading` / `read` / `important`，自动更新 reading-list.md |
| `paper_reading_stats()` | 查看阅读进度统计（各状态计数 + 最近论文） |
| `paper_note_add(paper_id, content)` | 添加笔记（用户手写或 AI 分析），自动同步到 `notes/{id}.md` |
| `paper_note_show(paper_id)` | 查看某篇论文的所有笔记 |
| `paper_group_create(name, description)` | 创建命名的论文分组，自动生成 `collections/{name}.md` |
| `paper_group_add(name, paper_ids)` | 向分组添加论文 |
| `paper_group_show(name)` | 查看分组内论文列表 |
| `paper_group_list()` | 列出所有分组及论文数 |
| `paper_citations(paper_id, direction)` | 通过 Semantic Scholar 查询引用/被引用关系，新论文自动入库，结果保存到 citation-traces/ |

### 导出与下载

| 工具 | 说明 |
|------|------|
| `paper_download(paper_ids)` | 批量下载 PDF（一次传多个 ID） |
| `paper_export(paper_ids, format)` | 导出 BibTeX / Markdown / JSON |

## Workspace 文件结构

运行 `paper_workspace_init()` 后，在项目目录下生成：

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
> 数据库是真相源，文件是"投影"——丢失可通过 `paper_workspace_init()` 重建。

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
