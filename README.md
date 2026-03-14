# Paper Agent

CLI-first paper intelligence system for AI researchers.

自动从 arXiv 收集论文，利用 LLM 按你的研究方向过滤评分，生成每日推荐摘要。

## Installation

### 一键安装为系统命令（推荐）

```bash
# clone 后直接跑安装脚本
./install.sh
```

脚本会自动：
1. 检查 Python 3.10+ 环境
2. 安装 pipx（如果没有）
3. 通过 pipx 将 `paper-agent` 安装为全局命令

安装完成后，在任何目录下都可以直接使用 `paper-agent`。

### 开发模式安装

如果你要修改源码，用以下方式安装：

```bash
cd paper_agent

# 方式一：Poetry（推荐）
poetry install
# 之后用 poetry run paper-agent 或 poetry shell 后使用

# 方式二：pip editable install
pip install -e .

```

### 卸载

```bash
pipx uninstall paper-agent
```

## User Journey

### Step 1: 初始化配置

首次使用前必须初始化，设定你的研究方向和 LLM 配置：

```bash
paper-agent init
```

交互式引导你填写：
- **研究方向** — 如 `retrieval-augmented generation, circuit design`
- **关键词** — 更细粒度的过滤词
- **arXiv 分类** — 从哪些分类收集，如 `cs.AI, cs.LG, cs.CL`
- **LLM Provider** — `anthropic` 或 `openai`
- **API Key** — 用于论文过滤和摘要生成
- **Base URL** — 自定义 API 端点（可选，留空使用默认）

配置保存在 `~/.paper-agent/config.yaml`，随时可以重新 `init` 覆盖。

#### 非交互式初始化（适合脚本/自动化）

也可以通过 CLI 参数直接初始化，跳过交互式提示：

```bash
paper-agent init \
  --provider openai \
  --api-key "sk-xxx" \
  --base-url "https://api.custom.com" \
  --topics "RAG, circuit design" \
  --keywords "transformer, attention" \
  --sources "cs.AI, cs.LG"
```

支持的参数：
- `--provider` — LLM 提供商（anthropic/openai）
- `--api-key` — API 密钥
- `--base-url` — 自定义 API 端点（用于代理、Azure OpenAI 等）
- `--model` — 模型名称（留空使用默认）
- `--topics` — 研究方向（逗号分隔）
- `--keywords` — 关键词（逗号分隔）
- `--sources` — arXiv 分类（逗号分隔）

也可以混合使用，例如只提供 API key，其他字段仍然交互式输入：

```bash
paper-agent init --api-key "sk-xxx"
```

### Step 2: 收集论文

从 arXiv 抓取最近的论文，并用 LLM 自动评分过滤：

```bash
paper-agent collect
```

常用选项：
| 选项 | 说明 | 默认值 |
|---|---|---|
| `-d, --days N` | 收集最近 N 天的论文 | 7 |
| `-m, --max N` | 每个分类最多抓取 N 篇 | 200 |
| `--no-filter` | 只收集不过滤（跳过 LLM 评分） | 默认过滤 |

```bash
# 示例：收集最近 3 天，每分类最多 100 篇
paper-agent collect -d 3 -m 100
```

### Step 3: 查看每日推荐

收集完成后，生成今天的论文推荐摘要：

```bash
paper-agent digest
```

会按置信度分为 **High Confidence**（强推荐）和 **Supplemental**（补充参考）两档展示。

```bash
# 查看指定日期的 digest
paper-agent digest --date 2026-03-10
```

### Step 4: 搜索论文

在本地论文库中关键词搜索：

```bash
paper-agent search "retrieval augmented generation"

# 限制返回数量
paper-agent search "transformer" -n 10
```

### Step 5: 查看论文详情

通过论文 ID 查看详细信息（标题、摘要、评分、链接等）：

```bash
paper-agent show <paper-id>
```

### Step 6: 查看统计

总览本地论文库的状态：

```bash
paper-agent stats
```

输出包括：总论文数、高/低置信度数量、未评分数量、热门 topic 排行。

## Interactive Mode (REPL)

直接运行 `paper-agent`（不带子命令）会进入交互式模式：

```bash
paper-agent
```

```
paper> collect -d 3
paper> digest
paper> search transformer
paper> show 1          # 用上一次结果的序号查看详情
paper> stats
paper> help
paper> quit
```

交互模式下 `show` 支持直接用结果列表的序号（如 `show 1` 查看第一篇），不需要手动复制 paper ID。

## JSON Output

所有命令都支持 `--json` 输出，方便脚本集成和自动化：

```bash
paper-agent digest --json
paper-agent search "LLM" --json
paper-agent stats --json
```

## Configuration

查看当前配置：

```bash
paper-agent config
```

API Key 也可以通过环境变量设置（优先级高于配置文件）：

```bash
export PAPER_AGENT_LLM_API_KEY="your-key-here"
```

## Typical Daily Workflow

```bash
# 每天早上跑一次
paper-agent collect -d 1        # 抓昨天的新论文
paper-agent digest              # 看今天的推荐

# 感兴趣的论文深入看
paper-agent show <paper-id>

# 随时搜索历史论文
paper-agent search "topic you care about"
```

## IDE Integration

除了 CLI，paper-agent 还可以通过 MCP（Model Context Protocol）集成到 AI 编码工具中，让你在写代码的同时直接搜索、分析论文。

### Cursor 集成

```bash
# 在你的项目目录中运行（会写入 .cursor/mcp.json + skill + rule）
paper-agent setup cursor

# 或全局安装（所有项目可用）
paper-agent setup cursor --scope global
```

配置完成后重启 Cursor，在 Agent chat 中直接说：
- "start my day" → 收集今日论文 + 生成推荐
- "搜索论文 transformer" → 搜索本地论文库
- "分析论文 2301.12345" → 生成结构化分析笔记

### Claude Code 集成

```bash
# 在你的项目目录中运行
paper-agent setup claude-code
# 写入：.mcp.json + .claude/commands/ + .claude/skills/ + CLAUDE.md + .paper-agent/

# 验证安装
paper-agent doctor

# 或全局注册 MCP server
paper-agent setup claude-code --scope global
```

配置完成后在该目录运行 `claude`，可以使用：

**主入口：**
- `/paper` → **统一入口**，展示功能菜单，不知道用哪个命令时从这里开始

**日常命令：**
- `/start-my-day` → `paper_morning_brief`: 一次调用完成 context + collect + digest + auto-mark（表格化展示 + 结论与建议）
- `/paper-search transformer` → 搜索论文库
- `/paper-analyze 2301.12345` → 深度分析 + 自动存笔记 + 标记状态
- `/paper-collect 7` → 三源并行采集
- `/paper-setup` → 对话式配置

**多篇智能：**
- `/paper-compare` → 多篇对比
- `/paper-survey AI for EDA` → `paper_quick_scan` quick-first 文献综述
- `/paper-download 2301.12345` → 下载 PDF
- "帮我找 Attention Is All You Need" → `paper_find_and_download` 精确查找 + 下载

**能力下沉工具（v03 新增）：**
- `/paper-triage` → `paper_auto_triage`: 自动按 profile 三档分流
- `/paper-insight GNN placement` → `paper_trend_data`: 趋势分析（按年×方向）
- `paper_citation_trace` → 递归引用追踪（2 层，一次调用）
- `paper_quick_scan` → 本地+在线搜索去重排序（替代 3 步 AI 链）

**Workspace：**
- `.paper-agent/` 目录：阅读进度、笔记、分组 → markdown 文件
- `paper_workspace_context()` 返回 `mode` 字段自动区分用户类型
- `paper_note_add(mark_as=)` / `paper_group_add(create_if_missing=True)` → 一步两操作

或直接自然语言："帮我找 RAG 相关的论文"

### 前置条件

IDE 集成依赖 paper-agent 已完成 LLM 初始化（因为要输入 API Key，这一步必须在终端）：

```bash
paper-agent init            # 配置 LLM provider 和 API key
paper-agent doctor          # 检查安装完整性
```

研究方向配置和论文收集可以在 IDE 内完成（Claude Code: `/paper-setup`，Cursor: 直接对话）。

### End-to-End 演示：从零到在 Claude Code 中用起来

下面是一个**完整的真实流程**，演示一个 AI 研究员如何从安装 paper-agent 到在 Claude Code 中日常使用。

#### Phase 1: 安装 + LLM 初始化（终端，约 2 分钟）

```bash
# 安装
pipx install paper-agent          # 全局安装，paper-agent 和 paper-agent-mcp 都可用

# 初始化 LLM（这一步必须在终端完成，因为要输入 API Key）
paper-agent init
#   LLM Provider: openai
#   API Key: sk-xxxxx
#   Base URL: (留空)
#   Model: (留空)
# ✅ 初始化完成！
```

#### Phase 2: 连接到 Claude Code（终端，约 10 秒）

```bash
# 在你自己的研究项目中运行（不是 paper-agent 源码目录）
cd ~/my-research-project

paper-agent setup claude-code
# ✅ MCP → .mcp.json
# ✅ Commands → .claude/commands  (/start-my-day, /paper-search, ..., /paper-setup)
# ✅ CLAUDE.md → CLAUDE.md
# ✅ Workspace → .paper-agent/
```

生成的文件：
```
my-research-project/
├── .mcp.json                     ← 告诉 Claude Code 启动 paper-agent-mcp
├── CLAUDE.md                     ← 告诉 AI 有哪些工具可用
├── .paper-agent/                 ← 研究工作台（仪表盘、日志、笔记、分组）
│   ├── README.md                 ← 自动更新的研究仪表盘
│   ├── research-journal.md       ← 研究日志
│   ├── reading-list.md           ← 阅读队列
│   ├── collections/              ← 论文分组
│   ├── notes/                    ← 论文笔记
│   └── citation-traces/          ← 引用链追踪
└── .claude/
    └── commands/
        ├── start-my-day.md       ← /start-my-day
        ├── paper-search.md       ← /paper-search
        ├── paper-analyze.md      ← /paper-analyze
        ├── paper-collect.md      ← /paper-collect
        ├── paper-setup.md        ← /paper-setup（配置研究方向）
        ├── paper-compare.md      ← /paper-compare（多篇对比）
        ├── paper-survey.md       ← /paper-survey（文献综述）
        ├── paper-download.md     ← /paper-download（PDF 下载）
        ├── paper-triage.md       ← /paper-triage（批量筛选）
        └── paper-insight.md      ← /paper-insight（趋势分析）
```

#### Phase 3: 在 Claude Code 里配置研究方向（对话式，约 3 分钟）

从这里开始，**不需要再回终端了**。启动 Claude Code：

```bash
cd ~/my-research-project
claude
```

```
You: /paper-setup

Claude: 你好！我来帮你配置 paper-agent 的研究方向。
        先看看有没有合适的模板...
        [调用 paper_templates_list()]

        有几个预设模板：
        1. ai-hardware — AI for Hardware Design (EDA, HLS, circuit design)
        2. nlp — Natural Language Processing
        3. cv — Computer Vision
        ...

        你的研究方向跟哪个比较接近？或者你也可以直接告诉我你在做什么研究。

You: 我做 EDA 方向的，主要关注用 AI 方法做电路设计，特别是 placement 和 routing

Claude: 明白！我根据 ai-hardware 模板 + 你的具体方向来配置：

        Topics:
        - circuit design, EDA, placement, routing
        - high-level synthesis, logic synthesis

        Keywords:
        - transformer, GNN, reinforcement learning
        - netlist, floorplan, timing optimization

        [调用 paper_sources_list()]

        推荐启用这些 arXiv 分类：
        - arxiv:cs.AR — Hardware Architecture
        - arxiv:cs.AI — Artificial Intelligence
        - arxiv:cs.LG — Machine Learning

        这样配置可以吗？需要调整吗？

You: 可以，再加一个 cs.PL 吧

Claude: [调用 paper_profile_update(
            topics=["circuit design", "EDA", "placement", "routing", ...],
            keywords=["transformer", "GNN", ...],
            enable_sources=["arxiv:cs.AR", "arxiv:cs.AI", "arxiv:cs.LG", "arxiv:cs.PL"]
        )]

        ✅ Profile 已保存！要不要现在就收集一周的论文试试？

You: 好

Claude: [调用 paper_collect(days=7)]

        ✅ 收集完成: 342 篇论文 (342 新增, 0 重复)
        ✅ 过滤完成: 342 篇论文已评分

        要看看今天的推荐吗？

You: /start-my-day
```

**关键区别**：研究方向的配置从"终端跑命令填表"变成了"跟 AI 聊天确定"。AI 可以基于对话理解你的需求，主动推荐 topics、keywords、sources。

#### Phase 4: 日常使用（每天）

Claude Code 读取 `.mcp.json`，自动启动 `paper-agent-mcp` 进程。

##### 场景 1: 早上开工 — `/start-my-day`

```
You: /start-my-day

Claude: 正在收集今日论文...
        [调用 paper_collect(days=1)]

        收集完成：47 篇新论文，已完成 LLM 评分。

        [调用 paper_digest()]

        📋 今日论文推荐 — 2026-03-13

        **高置信推荐**（8 篇）

        | # | 标题 | 评分 | 关键词 | 一句话总结 |
        |---|------|------|--------|-----------|
        | 1 | [[Attention Is All You Need for EDA]] | 9.2 | transformer, placement | 将 transformer 应用于电路布局优化，比传统方法快 3.2× |
        | 2 | [[GNN-Driven High-Level Synthesis]] | 8.7 | GNN, HLS | 用 GNN 预测 HLS 设计空间 Pareto 前沿 |
        | 3 | ... | ... | ... | ... |

        **结论与建议**: 今日论文主要聚焦 placement 和 HLS 两个方向。
        第 1 篇与你的 "circuit design + transformer" 方向高度匹配，建议优先阅读。

        深入看哪篇？保存今日摘要？还是先这样？
```

##### 场景 2: 写代码时查论文

```
You: 我在实现一个 attention-based placement engine，有没有相关论文？

Claude: [调用 paper_search("attention placement engine circuit")]

        找到 6 篇相关论文：

        | # | 标题 | 评分 | 关键词 | 一句话总结 |
        |---|------|------|--------|-----------|
        | 1 | AttentionPlacer: Transformer for Chip... | 8.9 | attention, placement | 首次将 cross-attention 用于 chip placement |
        | 2 | Self-Attention Mechanisms in VLSI Layout | 7.4 | self-attention, VLSI | self-attention 用于 VLSI 布局优化 |
        | 3 | DREAMPlace 4.0: Attention-Enhanced... | 8.1 | DREAMPlace, attention | DREAMPlace 加入 attention 机制 |

        **结论**: 第 1 篇和你的 attention-based placement engine 方向最接近，建议优先看。

        要看详细分析吗？

You: 第 1 篇展开

Claude: [调用 paper_show("arxiv:2601.03421")]

        📄 [[AttentionPlacer: Transformer for Chip Placement]]

        核心信息
        - 作者: Zhang et al. (2026)
        - 机构: PKU + ByteDance
        - 评分: 8.9/10

        摘要翻译
        > 本文提出 AttentionPlacer，将 multi-head attention 机制
        > 引入芯片布局优化。通过将 netlist 表示为图序列...

        方法概述
        1. 将电路 netlist 转化为 token 序列
        2. 使用 cross-attention 捕获 cell 间的连接关系
        3. 迭代式 placement refinement...

        与你代码的关联
        你当前实现的 attention-based placement engine 可以参考
        他们的 cross-attention 设计（Section 3.2），特别是
        position encoding 的处理方式。

You: 帮我把这篇的核心方法记到 notes/attention-placement.md

Claude: [写入文件 notes/attention-placement.md]

        ✅ 已保存分析笔记到 notes/attention-placement.md
```

##### 场景 3: Cursor 中的等价体验

在 Cursor 里没有 slash 命令，但通过 Skill + Rule 实现相同效果：

```
You: start my day

Agent: [识别到论文相关意图，触发 paper-agent skill]
       [调用 MCP tool: paper_collect(days=1)]
       [调用 MCP tool: paper_digest()]

       （展示同样的推荐列表）

You: 搜索论文 LoRA fine-tuning for hardware design

Agent: [调用 MCP tool: paper_search("LoRA fine-tuning hardware design")]

       （展示搜索结果）
```

#### 对比总结

| | 纯 CLI | CLI + IDE (MCP 集成) |
|---|---|---|
| 查论文 | 切终端 → 输命令 → 看结果 → 切回 IDE | 在对话框直接说 → 看结果 |
| 每日推荐 | 手动跑 2 条命令 | `/start-my-day` 一步完成 |
| 分析论文 | show → 自己读 → 自己写笔记 | 说一句话 → AI 生成结构化笔记并保存 |
| 上下文 | 手动在终端和 IDE 间切换 | AI 知道你在写什么代码，能关联推荐 |
| 语言 | 英文命令 + 英文输出 | 自然语言输入，中文输出 |
