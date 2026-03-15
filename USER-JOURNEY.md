# Paper Agent — 用户旅程

从安装到日常使用的完整指南。

---

## 第一章：安装

### 方式 A：pipx 全局安装（推荐）

```bash
pipx install paper-agent
```

安装完成后你会得到两个全局命令：
- `paper-agent` — CLI 主程序
- `paper-agent-mcp` — MCP 服务器（给 IDE 集成用的，不需要手动运行）

### 方式 B：从源码安装（开发者）

```bash
git clone <repo-url>
cd paper_agent
poetry install
```

之后用 `poetry run paper-agent` 或 `poetry shell` 后直接用 `paper-agent`。

### 验证安装

```bash
paper-agent --help
```

看到命令列表说明安装成功。

---

## 第二章：初始化

### Step 1：配置 LLM

```bash
paper-agent init
```

系统会交互式询问：

```
LLM Provider (anthropic/openai): openai
API Key: sk-xxxxx
Base URL (留空使用默认):
Model (留空使用默认):

✅ 初始化完成！配置已保存到 ~/.paper-agent/config.yaml
```

也可以一行搞定（适合脚本化）：

```bash
paper-agent init --provider openai --api-key "sk-xxx"
```

### Step 2：创建研究 Profile

```bash
paper-agent profile create
```

系统引导你设定研究方向：

```
选择入口: template 还是 manual?
> template

可用模板：
  1. ai-hardware — AI for Hardware Design (EDA, HLS, circuit design)
  2. nlp — Natural Language Processing
  3. cv — Computer Vision
  4. ml-theory — Machine Learning Theory

选择: 1

Topics: circuit design, EDA, high-level synthesis, logic synthesis
Keywords: transformer, GNN, reinforcement learning, netlist

推荐启用以下 arXiv 分类：
  arxiv:cs.AR — Hardware Architecture
  arxiv:cs.AI — Artificial Intelligence
  arxiv:cs.LG — Machine Learning
启用？(Y/n): Y

✅ Profile 已保存！
提示：运行 paper-agent collect 开始收集论文
```

### Step 3：管理论文来源

```bash
# 查看所有可用来源
paper-agent sources list

# 启用额外分类
paper-agent sources enable arxiv:cs.PL arxiv:cs.SE

# 禁用不需要的
paper-agent sources disable arxiv:cs.CV
```

---

## 第三章：日常使用

### 3.1 收集论文

```bash
# 收集最近 7 天（默认）
paper-agent collect

# 收集最近 1 天（日常用）
paper-agent collect -d 1

# 只收集不评分（快速）
paper-agent collect --no-filter

# 排查 0 篇问题
paper-agent collect --debug
```

输出示例：

```
正在收集 arXiv 论文...
  cs.AR: 45 篇
  cs.AI: 128 篇
  cs.LG: 167 篇

收集完成: 340 篇论文 (312 新增, 28 重复)
LLM 过滤中... ████████████████████████ 312/312
过滤完成: 312 篇论文已评分
```

### 3.2 查看每日推荐

```bash
paper-agent digest
```

输出示例：

```
═══ Digest — 2026-03-13 ═══
Library: 1,247 | Filtered: 312

── High Confidence (8 篇) ──

1. Attention Is All You Need for EDA
   作者: Zhang et al.   评分: 9.2/10
   将 transformer 架构应用于电路布局优化

2. GNN-Driven High-Level Synthesis
   作者: Li et al.      评分: 8.7/10
   用图神经网络预测 HLS 设计空间

...

── Supplemental (15 篇) ──
...
```

查看历史：

```bash
paper-agent digest --date 2026-03-10
```

### 3.3 搜索论文

```bash
paper-agent search "reinforcement learning placement"
```

输出示例：

```
找到 12 篇相关论文：

  #  │ 标题                                    │ 评分  │ 日期
─────┼─────────────────────────────────────────┼───────┼──────────
  1  │ RL-Placer: Reinforcement Learning...    │ 9.1   │ 2026-02-15
  2  │ Deep RL for Macro Placement             │ 8.4   │ 2026-01-20
  3  │ Graph RL Chip Floorplanning             │ 7.8   │ 2025-12-03
  ...

输入 paper-agent show <ID> 查看详情
```

限制结果数量：

```bash
paper-agent search "transformer" -n 5
```

### 3.4 查看论文详情

```bash
paper-agent show <paper-id>
```

输出示例：

```
╭─ Paper Detail ─────────────────────────────────────────╮
│ Title:    RL-Placer: Reinforcement Learning for...     │
│ Authors:  Zhang, Li, Wang                              │
│ Source:   arxiv                                        │
│ ID:       arxiv:2602.01234                             │
│ Date:     2026-02-15                                   │
│ URL:      https://arxiv.org/abs/2602.01234             │
│                                                        │
│ Score:    9.1 / 10  (high)                             │
│ Reason:   与 EDA + RL 方向高度匹配                      │
│ Topics:   cs.AR, cs.AI                                 │
│                                                        │
│ Abstract:                                              │
│ We propose RL-Placer, a novel reinforcement learning   │
│ framework for chip macro placement that achieves...    │
╰────────────────────────────────────────────────────────╯
```

### 3.5 查看统计

```bash
paper-agent stats
```

输出示例：

```
═══ Library Stats ═══
Total papers:     1,247
High confidence:  156
Low confidence:   891
Unscored:         200

Top Topics:
  cs.AI         342
  cs.LG         287
  cs.AR         198
  ...
```

### 3.6 查看配置

```bash
paper-agent config

# 显示完整 API key
paper-agent config --show-secrets
```

---

## 第四章：交互模式（REPL）

直接运行 `paper-agent` 进入交互模式：

```bash
$ paper-agent

paper> collect -d 1
收集完成: 47 篇论文 (42 新增, 5 重复)

paper> digest
(展示今日推荐)

paper> search transformer
找到 8 篇相关论文...

paper> show 1
(用序号直接查看第一条搜索结果)

paper> stats
(展示统计)

paper> help
(查看所有命令)

paper> quit
```

交互模式的优势：
- 不需要每次输入 `paper-agent` 前缀
- `show` 支持用搜索结果序号，不需要复制 paper ID
- `search` 有别名 `s`
- 输入未知命令会当作搜索关键词

---

## 第五章：JSON 输出（自动化/Agent）

所有主要命令都支持 `--json`：

```bash
paper-agent digest --json > digest_$(date +%Y%m%d).json
paper-agent search "LLM" --json
paper-agent stats --json
paper-agent show <id> --json
```

适合：
- cron job 自动化
- 脚本解析
- 与其他工具集成

---

## 第六章：连接 IDE

Paper-agent 通过 MCP 协议连接 AI IDE，让你在写代码时直接用自然语言操作论文库。

### Claude Code

```bash
cd ~/my-research-project
paper-agent setup claude-code
```

详细使用指南见 → [plugin/USER-JOURNEY.md](plugin/USER-JOURNEY.md)

### Cursor

```bash
cd ~/my-research-project
paper-agent setup cursor
```

之后在 Cursor Agent chat 中直接说：
- "start my day" → 收集 + 推荐
- "搜索论文 transformer" → 搜索
- "分析论文 2301.12345" → 结构化分析

### 全局 vs 项目级

```bash
# 项目级（默认）— 仅当前目录生效
paper-agent setup claude-code

# 全局 — 所有目录生效
paper-agent setup claude-code --scope global
```

---

## 第七章：典型工作日

```
08:00  paper-agent collect -d 1        # 收集昨天的新论文
       paper-agent digest              # 查看今日推荐

08:15  paper-agent show <paper-id>     # 深入看感兴趣的

10:30  paper-agent search "attention mechanism"   # 写代码时查论文

14:00  paper-agent search "LoRA fine-tuning" -n 5  # 查特定方向

17:00  paper-agent stats               # 看看库的积累情况
```

或者在 Claude Code 中一句 `/start-my-day` 搞定早上的流程。

---

## 第八章：常见问题

### 收集到 0 篇论文

```bash
paper-agent collect --debug    # 查看请求详情
paper-agent sources list       # 确认有已启用的来源
paper-agent config             # 确认配置正确
```

### 高置信论文太少

说明 topics/keywords 和收集到的论文不匹配：

```bash
paper-agent profile create     # 重新配置研究方向
paper-agent collect -d 14      # 扩大收集范围
```

### API Key 问题

```bash
# 通过环境变量设置（优先级高于配置文件）
export PAPER_AGENT_LLM_API_KEY="your-key-here"

# 或重新初始化
paper-agent init
```

### 数据库问题

```bash
# 检查完整性
sqlite3 ~/.paper-agent/library.db "PRAGMA integrity_check;"

# 重建（会丢失已有数据）
rm ~/.paper-agent/library.db
paper-agent init
paper-agent collect -d 30
```

---

## 命令速查表

| 命令 | 用途 | 常用参数 |
|------|------|---------|
| `paper-agent init` | 初始化 LLM 配置 | `--provider`, `--api-key` |
| `paper-agent profile create` | 创建研究 Profile | — |
| `paper-agent sources list` | 查看论文来源 | `--json` |
| `paper-agent sources enable <id>` | 启用来源 | — |
| `paper-agent collect` | 收集论文 | `-d 天数`, `-m 最大数`, `--no-filter` |
| `paper-agent digest` | 每日推荐 | `--date`, `--json` |
| `paper-agent search "<query>"` | 搜索论文 | `-n 数量`, `--json` |
| `paper-agent show <id>` | 论文详情 | `--json` |
| `paper-agent stats` | 库统计 | `--json` |
| `paper-agent config` | 查看配置 | `--show-secrets` |
| `paper-agent setup cursor` | 配置 Cursor 集成 | `--scope global` |
| `paper-agent setup claude-code` | 配置 Claude Code 集成 | `--scope global` |

---

## 数据文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| 配置文件 | `~/.paper-agent/config.yaml` | topics, keywords, sources, LLM 配置 |
| 论文数据库 | `~/.paper-agent/library.db` | SQLite，所有论文数据 |
| Digest 文件 | `~/.paper-agent/artifacts/digests/` | 每日 digest markdown |
| Sources 覆盖 | `~/.paper-agent/sources.yaml` | 来源启用/禁用状态 |
