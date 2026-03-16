<h1 align="center">📄 Paper Agent</h1>

<p align="center">
  <strong>AI-powered research paper intelligence for researchers who live in their IDE.</strong>
</p>

<p align="center">
  自动从 arXiv / Semantic Scholar / DBLP 收集论文，LLM 智能评分过滤，生成每日推荐。<br/>
  与 Claude Code / Cursor 深度集成，Obsidian 知识库实时同步。
</p>

---

## ✨ Features

- **三源并行采集** — arXiv + Semantic Scholar + DBLP，覆盖预印本和会议论文
- **LLM 智能评分** — 按你的研究方向自动过滤、评分、分流
- **每日推荐** — 一句 "start my day" 完成采集→评分→推荐→标记
- **深度分析** — 单篇分析、多篇对比、文献综述、引用追踪、趋势洞察
- **Obsidian 知识库** — 论文自动同步为 Markdown，Dataview 动态查询，Graph View 关联可视化
- **IDE 原生集成** — Claude Code slash 命令 / Cursor MCP skill，不离开编辑器
- **CLI + REPL** — 终端党也能用，所有功能命令行可达

## 🚀 Quick Start

### 安装

```bash
# 方式一：pipx 全局安装（推荐）
pipx install paper-agent

# 方式二：开发模式
git clone https://github.com/linshaoxin-maker/PaperClaw.git
cd PaperClaw
pip install -e .
```

### 初始化

```bash
paper-agent init
```

交互式配置：研究方向、关键词、arXiv 分类、LLM Provider + API Key。

也支持非交互式：

```bash
paper-agent init \
  --provider openai \
  --api-key "sk-xxx" \
  --topics "RAG, circuit design" \
  --keywords "transformer, attention" \
  --sources "cs.AI, cs.LG"
```

### IDE 集成

```bash
# Claude Code
paper-agent setup claude-code

# Cursor
paper-agent setup cursor
```

### Obsidian 知识库

IDE 集成后，`.paper-agent/` 目录就是你的 Obsidian vault：

1. 打开 Obsidian → "Open folder as vault" → 选择项目下的 `.paper-agent/`
2. 安装 Dataview 插件（Community plugins → Dataview）
3. 完成。所有论文、报告、查询页自动就位

## 📁 Workspace 结构

```
.paper-agent/
├── 00-Dashboard.md          ← 研究仪表盘（Dataview 实时查询）
├── 研究日志.md               ← AI 自动记录每次操作
├── 阅读清单.md               ← 按状态分组的阅读队列
│
├── 01-每日推荐/              ← 每日论文推荐（按日期归档）
├── 02-论文库/                ← 论文 Markdown 文件 + Dataview 查询页
│   ├── _高分论文.md
│   ├── _按方法分类.md
│   ├── _按年份分布.md
│   ├── _按会议分类.md
│   ├── _按分组分类.md
│   ├── _最近入库.md
│   ├── _阅读进度.md
│   └── Paper_Title_2025-03-16.md  ← 每篇论文一个文件
│
├── 03-深度分析/              ← 单篇深度分析报告
├── 04-对比分析/              ← 多篇对比报告
├── 05-文献综述/              ← 文献综述
├── 06-趋势洞察/              ← 趋势分析报告
├── 07-阅读包/                ← 主题阅读包
├── 08-研究Ideas/             ← AI 生成的研究想法
├── 09-实验计划/              ← 实验方案
├── 10-引用追踪/              ← 引用链追踪
├── 11-论文分组/              ← 论文分组文件
├── 12-搜索结果/              ← 搜索结果存档
├── 13-筛选报告/              ← 筛选分流报告
│
├── .data/                    ← 系统文件（Obsidian 中隐藏）
│   ├── config.yaml
│   ├── library.db
│   └── artifacts/
└── .obsidian/                ← Obsidian 预配置（自动生成）
```

## 🔬 Daily Workflow

### CLI 用户

```bash
paper-agent collect -d 1     # 采集昨天的新论文
paper-agent digest           # 生成今日推荐
paper-agent search "topic"   # 搜索论文库
paper-agent show <paper-id>  # 查看论文详情
paper-agent stats            # 论文库统计
```

### IDE 用户（Claude Code / Cursor）

```
You: start my day
→ 自动采集 + 评分 + 推荐 + 保存报告 + 同步到 Obsidian

You: 搜索论文 transformer placement
→ 本地 + 在线搜索，结果表格化展示

You: 分析这篇 2301.12345
→ 深度分析 + 自动存笔记 + 标记状态

You: 帮我做一个 GNN for EDA 的文献综述
→ 搜索 + 筛选 + 生成综述报告 + 保存
```

### Obsidian 联动

所有 Claude 生成的报告自动保存为 Markdown，Obsidian 实时显示：

- **Dashboard** — Dataview 实时统计论文数、阅读进度、分组概览
- **查询页** — 按方法/年份/来源/分组分类浏览，每个分类下展开论文列表
- **Graph View** — 论文之间通过 wikilink 和 tag 关联，可视化知识网络
- **论文文件** — 带 YAML frontmatter（title, authors, year, score, tags, groups, date），支持 Dataview 查询

## 🛠 MCP Tools（59+）

| 类别 | 工具 | 说明 |
|------|------|------|
| **搜索** | `paper_search` | 本地 FTS5 搜索 |
| | `paper_search_batch` | 多方向批量搜索 |
| | `paper_search_online` | arXiv + S2 在线搜索 |
| **采集** | `paper_collect` | 三源并行采集 |
| | `paper_survey_collect` | 回溯 N 年论文采集 |
| **分析** | `paper_show` | 单篇详情 |
| | `paper_batch_show` | 批量查看 |
| | `paper_compare` | 结构化对比 |
| **智能** | `paper_morning_brief` | 一键每日推荐 |
| | `paper_auto_triage` | 自动三档分流 |
| | `paper_citation_trace` | 递归引用追踪 |
| | `paper_trend_data` | 趋势统计 |
| | `paper_quick_scan` | 快速扫描 |
| **报告** | `paper_save_report` | 保存报告 + 自动同步论文到 Obsidian |
| | `paper_list_reports` | 列出已保存报告 |
| **Obsidian** | `paper_sync_vault` | 批量同步论文到 02-论文库/ |
| | `paper_export` | 导出 BibTeX / Markdown / Obsidian / JSON |
| **Workspace** | `paper_workspace_status` | 仪表盘 |
| | `paper_reading_status` | 设置阅读状态 |
| | `paper_note_add` | 添加笔记 |
| | `paper_group_add` | 论文分组 |
| | `paper_download` | 下载 PDF |

完整工具列表：`paper-agent doctor`

## ⚙️ Configuration

```bash
paper-agent config           # 查看当前配置
paper-agent doctor           # 检查安装完整性
```

环境变量（优先级高于配置文件）：

```bash
export PAPER_AGENT_LLM_API_KEY="your-key"
export PAPER_AGENT_DATA_DIR="/custom/path"   # 自定义数据目录
```

## 📦 Claude Code Commands

| 命令 | 功能 |
|------|------|
| `/paper` | 统一主入口，智能路由 |
| `/start-my-day` | 每日推荐 |
| `/paper-search` | 搜索论文 |
| `/paper-analyze` | 深度分析 |
| `/paper-compare` | 多篇对比 |
| `/paper-survey` | 文献综述 |
| `/paper-triage` | 批量筛选 |
| `/paper-insight` | 趋势分析 |
| `/paper-citation` | 引用追踪 |
| `/paper-plan` | 研究规划 |
| `/paper-download` | 下载 PDF |

## License

MIT
