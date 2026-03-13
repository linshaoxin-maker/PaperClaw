# Paper Agent — Product Overview

**Version:** v01 + v02 (implemented)
**Last Updated:** 2026-03-13

## 1. 产品定位

Paper Agent 是一个 **AI 研究员的论文智能助手**。研究员通过 **Claude Code**（主要交互界面）与 paper-agent 协作，完成论文全链路工作。

### 1.1 交互架构

所有交互都发生在 Claude Code 里。研究员和 AI 对话，AI 按需调用 paper-agent 的 MCP 工具。

```
┌─ Claude Code (交互层) ──────────────────────────────────┐
│                                                          │
│  研究员 ←──对话──→ AI 模型                               │
│                      │                                   │
│                      ├─ 理解意图                         │
│                      ├─ 提取关键词                       │
│                      ├─ 调用 MCP tool ────→ paper-agent  │
│                      ├─ 格式化结果                       │
│                      ├─ 追问确认                         │
│                      ├─ 弹出选择 UI (Elicitation)        │
│                      └─ 写入文件                         │
│                                                          │
│  输入: 自然语言 / slash 命令 / checkbox 勾选             │
│  输出: 中文分析 / 表格 / markdown 文件 / BibTeX          │
└──────────────────────────────────────────────────────────┘
                          │ MCP 协议 (stdio)
                          ↓
┌─ paper-agent-mcp (数据层) ──────────────────────────────┐
│  收集 · 存储 · 检索 · 评分 · Profile 管理               │
│  SQLite 论文库 · arXiv 抓取 · LLM 过滤                  │
└─────────────────────────────────────────────────────────┘
```

### 1.2 核心原则

- **交互归 Claude Code**：对话、理解、分析、合成、呈现、文件写入
- **数据归 paper-agent**：收集、存储、检索、评分、Profile 管理
- **每个环节都有对话**：不是"调 API 返回结果"，是研究员和 AI 的多轮协作

### 1.3 不是什么

- 不是 reference manager（不替代 Zotero/Mendeley）
- 不是笔记系统（不替代 Obsidian/Notion）
- 不是 PDF 阅读器

---

## 2. 研究员论文工作流全景

一个 AI 研究员处理论文的完整链路，每个环节都有研究员和 Claude Code 之间的交互：

```
定位 → 搜索 → 筛选 → 下载 → 阅读 → 分析 → 对比 → 综述 → 导出 → 追踪
```

### 2.1 各环节交互详解

---

#### ① 定位 — 确定搜索目标

研究员往往不是带着精确关键词来的，而是带着一个模糊的研究问题。

**交互流程：**
```
研究员: "我最近在做 chip placement，想看看有没有用 RL 方法的论文"

Claude Code:
  ├─ 理解意图：用户想找 reinforcement learning + chip placement 论文
  ├─ 分析上下文：用户在 EDA 方向，关注 placement 问题
  ├─ 提取关键词：
  │   ├─ 主关键词: reinforcement learning, chip placement
  │   ├─ 扩展词: floorplanning, VLSI, macro placement
  │   └─ arXiv 分类: cs.AR, cs.AI, cs.LG
  └─ 确认: "我理解你要找 RL 做 chip placement 的论文，
            关键词用这些可以吗？需要补充吗？"

研究员: "加上 graph neural network 吧"

Claude Code: "好的，搜索关键词确认：
             reinforcement learning, chip placement, GNN, floorplanning
             开始搜索？"
```

| | v01 | v02 |
|---|---|---|
| paper-agent | — | — (不需要，这是 AI 的活) |
| Claude Code | ⚠️ 可以做但没有引导 | ✅ 主动分析、扩展关键词、确认 |
| 交互 | 用户直接给关键词 | AI 帮用户想关键词 → 确认 → 再搜 |

---

#### ② 搜索 — 查找论文

**交互流程：**
```
Claude Code:
  ├─ [调用 paper_search("RL chip placement GNN")]
  ├─ 本地库找到 8 篇
  ├─ "本地库找到 8 篇，要不要从 arXiv 再搜一下补充？" ← 交互点
  
研究员: "搜一下吧"

Claude Code:
  ├─ [调用 paper_search_online("reinforcement learning chip placement")]  (v02)
  ├─ 线上找到 25 篇新的
  └─ 合并后展示：共 33 篇候选

研究员: "太多了，只看 2024 年以后的"

Claude Code:
  ├─ 按时间过滤 → 18 篇
  └─ 重新展示
```

| | v01 | v02 |
|---|---|---|
| paper-agent | ✅ `paper_search` 本地库 | ✅ `paper_search_online` 联网 |
| Claude Code | 展示结果 | ✅ 判断是否补充搜索 → 追问 → 过滤 |
| 交互 | 搜一次看结果 | 搜 → 问够不够 → 补搜 → 过滤 → 满意为止 |

---

#### ③ 筛选 — 选择感兴趣的论文

**交互流程：**
```
Claude Code:
  ├─ 展示 18 篇候选列表（标题、评分、一行摘要）
  └─ [弹出 checkbox UI via MCP Elicitation]  (v02)
  
研究员: ✅ 勾选 6 篇感兴趣的

Claude Code:
  ├─ "你选了 6 篇。要做什么？"
  │   a) 逐篇阅读详情
  │   b) 方法对比
  │   c) 生成综述
  │   d) 先下载 PDF
  └─ 等待指令
```

| | v01 | v02 |
|---|---|---|
| paper-agent | ✅ LLM 自动评分 + digest | ✅ `paper_select` (Elicitation checkbox) |
| Claude Code | 展示列表，用户口头说编号 | ✅ 弹出 checkbox，用户勾选 |
| 交互 | "选 1, 3, 5"（对话式） | checkbox 勾选 → 选完问下一步做什么 |

---

#### ④ 下载 — 获取 PDF 全文

**交互流程：**
```
研究员: "帮我把选中的 6 篇都下载一下"

Claude Code:
  ├─ [调用 paper_download(paper_ids)]  (v02)
  ├─ "6 篇 PDF 已下载到 papers/ 目录：
  │    papers/2024-rl-placement.pdf
  │    papers/2023-gnn-floorplan.pdf
  │    ..."
  └─ "要我帮你读哪篇？"

研究员: "先读第一篇"
```

| | v01 | v02 |
|---|---|---|
| paper-agent | ❌ | ✅ `paper_download` |
| Claude Code | — | ✅ 批量下载 → 报告路径 → 追问下一步 |
| 交互 | 用户自己去 arXiv 下载 | 一句话下载 → 问读哪篇 |

---

#### ⑤ 阅读 — 理解论文内容

**交互流程：**
```
Claude Code:
  ├─ [调用 paper_show(paper_id)] → 摘要 + 元数据
  ├─ 展示论文核心信息（中文）
  └─ "要我展开讲方法部分吗？还是看完整摘要？"

研究员: "翻译一下摘要，然后总结三个要点"

Claude Code:
  ├─ 翻译摘要为中文
  ├─ 提炼三个核心要点
  └─ "要深入分析这篇吗？还是继续看下一篇？"
```

| | v01 | v02 |
|---|---|---|
| paper-agent | ✅ `paper_show` 摘要+元数据 | 🔲 提供全文（依赖 PDF 下载） |
| Claude Code | ✅ 翻译 + 总结 | ✅ 全文辅助阅读 |
| 交互 | 看详情 → 自己理解 | 看详情 → AI 翻译/总结 → 追问 → 深入或下一篇 |

---

#### ⑥ 分析 — 深度分析单篇

**交互流程：**
```
研究员: "帮我深度分析这篇"  或  /paper-analyze 2301.12345

Claude Code:
  ├─ [调用 paper_show(paper_id)]
  ├─ 生成结构化分析笔记：
  │   ├─ 核心信息 / 摘要翻译
  │   ├─ 方法概述
  │   ├─ 实验结果
  │   └─ 深度分析（优势、局限、适用场景）
  └─ "分析完成。要保存到文件吗？保存到哪个路径？"

研究员: "保存到 notes/rl-placement-analysis.md"

Claude Code:
  ├─ [写入文件]
  └─ "✅ 已保存。要继续分析下一篇吗？"
```

| | v01 | v02 |
|---|---|---|
| paper-agent | ✅ `paper_show` 提供数据 | 🔲 全文数据 |
| Claude Code | ✅ `/paper-analyze` 生成结构化笔记 | ✅ 更深入（含全文分析） |
| 交互 | 分析 → 展示 | 分析 → 展示 → 问保存路径 → 保存 → 问下一步 |

---

#### ⑦ 对比 — 多篇横向比较

**交互流程：**
```
研究员: "把选中的 6 篇做个方法对比"

Claude Code:
  ├─ [调用 paper_batch_show(6 篇 IDs)]  (v02)
  ├─ "你想从哪些维度对比？"
  │   a) 方法架构
  │   b) 实验结果 (benchmark)
  │   c) 适用场景
  │   d) 全部
  │   └─ [弹出选择 UI]

研究员: ✅ 方法架构  ✅ 实验结果

Claude Code:
  ├─ 生成对比表格：
  │   | 论文 | 方法 | 模型架构 | HPWL 改进 | 运行时间 |
  │   |------|------|---------|----------|---------|
  │   | A    | RL   | ...     | -12%     | 4h      |
  │   | B    | GNN  | ...     | -8%      | 1h      |
  │   | ...  |      |         |          |         |
  ├─ 分析总结：哪些方法更好、trade-off 是什么
  └─ "要保存这个对比表格吗？或者基于这些写 survey？"
```

| | v01 | v02 |
|---|---|---|
| paper-agent | ❌ | ✅ `paper_batch_show` + `paper_compare` (已实现) |
| Claude Code | ❌ | ✅ 选维度 → 生成对比 → 分析 → 追问 |
| 交互 | 不支持 | 选论文 → 选维度 → 对比 → 问保存/写 survey |

---

#### ⑧ 综述 — 生成 survey

**交互流程：**
```
研究员: "基于这些论文帮我写个 survey"

Claude Code:
  ├─ "survey 的主题是什么？"

研究员: "Reinforcement Learning Methods for Chip Placement"

Claude Code:
  ├─ "你希望 survey 包含哪些部分？"
  │   a) Background & Motivation
  │   b) 方法分类与对比
  │   c) 实验结果汇总
  │   d) Open Problems
  │   e) 全部
  │   └─ [弹出选择 UI]

研究员: ✅ 全选

Claude Code:
  ├─ [调用 paper_batch_show(所有选中论文)]
  ├─ 生成 survey 草稿（含引用、分类、趋势分析）
  ├─ "survey 草稿已生成（约 3000 字），先看看？"
  └─ 展示草稿

研究员: "Background 部分太短了，加一些 chip placement 的传统方法背景"

Claude Code:
  ├─ 补充传统方法背景
  └─ "修改完成。保存到 survey/rl-placement-survey.md？"

研究员: "好的，顺便导出引用的 BibTeX"

Claude Code:
  ├─ [写入 survey 文件]
  ├─ [调用 paper_export(IDs, format="bibtex")]  或自己生成
  └─ "✅ survey 和 refs.bib 已保存"
```

| | v01 | v02 |
|---|---|---|
| paper-agent | ❌ | ✅ `paper_batch_show` + `paper_export` (已实现) |
| Claude Code | ❌ | ✅ 选主题 → 选章节 → 生成 → 修改 → 保存 |
| 交互 | 不支持 | 主题 → 章节 → 草稿 → 反馈修改 → 保存 + 导出 |

---

#### ⑨ 导出 — 输出成果物

**交互流程：**
```
研究员: "帮我导出这批论文的 BibTeX"

Claude Code:
  ├─ [调用 paper_export(IDs, format="bibtex")]  (v02)
  ├─ "导出到哪个文件？"

研究员: "refs/placement.bib"

Claude Code:
  ├─ [写入文件]
  └─ "✅ 已导出 6 条 BibTeX 到 refs/placement.bib"
```

| | v01 | v02 |
|---|---|---|
| paper-agent | ⚠️ JSON 输出 | ✅ `paper_export` BibTeX/markdown/JSON |
| Claude Code | ⚠️ 可手动写文件 | ✅ 问路径 → 写入 |
| 交互 | 手动 | 选格式 → 选路径 → 导出 |

---

#### ⑩ 追踪 — 持续关注

**交互流程：**
```
# 每天早上
研究员: /start-my-day

Claude Code:
  ├─ [调用 paper_collect(days=1)]
  ├─ [调用 paper_digest()]
  ├─ "今日新增 23 篇，推荐 5 篇高置信论文："
  │   1. [[xxx]] — 9.1/10 — 跟你的 RL placement 方向直接相关
  │   2. ...
  └─ "要看哪篇？还是跳过今天的推荐？"

研究员: "第 1 篇展开"

Claude Code:
  ├─ [调用 paper_show()]
  └─ 展示详情 + "要深入分析吗？"
```

| | v01 | v02 |
|---|---|---|
| paper-agent | ✅ `paper_collect` + `paper_digest` | 🔲 作者追踪、引用提醒 |
| Claude Code | ✅ 展示推荐 | ✅ 推荐 → 追问 → 展开 → 分析 |
| 交互 | /start-my-day → 看列表 | 推荐 → 问看哪篇 → 展开 → 问下一步 |

---

### 2.2 交互设计总结

每个环节的交互模式都遵循同一个循环：

```
研究员发起（自然语言 / slash 命令）
    ↓
Claude Code 理解意图 → 确认/澄清
    ↓
调用 MCP tool(s) → 获取数据
    ↓
格式化呈现（中文、表格、wikilink）
    ↓
追问下一步（保存？继续？切换？）
    ↓
研究员反馈 → 循环
```

**Claude Code 在每个环节都不只是"调 API"**，而是：
- **理解**：把模糊的描述转化为精确的查询
- **确认**：不确定时主动追问
- **呈现**：把 JSON 转化为人类友好的格式
- **引导**：每步结束后建议下一步
- **修改**：结果不满意时支持迭代

---

## 3. v01 — 当前能力

### 3.1 架构

```
┌─ Claude Code (交互层) ──────────────────────────────────┐
│  /start-my-day · /paper-search · /paper-analyze         │
│  /paper-collect · /paper-setup · 自然语言               │
│  /paper-compare · /paper-survey · /paper-download (v02) │
│  理解意图 · 提取关键词 · 格式化 · 写文件 · 追问         │
└──────────────────────────┬──────────────────────────────┘
                           │ MCP 协议 (stdio)
┌─ paper-agent-mcp (数据层) ──────────────────────────────┐
│  v01 Tools:                                              │
│    paper_search · paper_show · paper_collect              │
│    paper_digest · paper_stats · paper_profile             │
│    paper_profile_update · paper_sources_list              │
│    paper_sources_enable · paper_templates_list            │
│  v02 Tools:                                              │
│    paper_batch_show · paper_compare                       │
│    paper_export · paper_download · paper_search_online    │
│  Resources:                                              │
│    paper://digest/today · paper://stats                   │
│    paper://profile · paper://recent                       │
└──────────────────────────┬──────────────────────────────┘
                           │
┌─ 核心层 ────────────────────────────────────────────────┐
│  SQLite 论文库 · LLM 过滤 & 评分 · arXiv 抓取 · 配置    │
└─────────────────────────────────────────────────────────┘
```

### 3.2 交互能力覆盖（v01 + v02）

| 环节 | 交互支持 | MCP Tool | Claude Code 命令 |
|------|---------|----------|-----------------|
| 定位 | ⚠️ | — (AI 的活) | 自然语言分析关键词 |
| 搜索 | ✅ | `paper_search` + `paper_search_online` | `/paper-search` |
| 筛选 | ✅ | LLM 评分 + digest | `/start-my-day` |
| 下载 | ✅ | `paper_download` | `/paper-download` |
| 阅读 | ✅ | `paper_show` + `paper_batch_show` | 自然语言 |
| 分析 | ✅ | `paper_show` | `/paper-analyze` |
| 对比 | ✅ | `paper_compare` + `paper_batch_show` | `/paper-compare` |
| 综述 | ✅ | `paper_batch_show` + `paper_export` | `/paper-survey` |
| 导出 | ✅ | `paper_export` (BibTeX/md/JSON) | 命令内集成 |
| 追踪 | ✅ | `paper_collect` + `paper_digest` | `/start-my-day` |

### 3.3 用户旅程（Claude Code 为主交互界面）

```
Day 0 — 安装（终端，5 分钟）
├─ pipx install paper-agent
├─ paper-agent init (配 API key)
└─ paper-agent setup claude-code (配 MCP + commands)

Day 1 — 首次使用（Claude Code）
├─ /paper-setup
│   ├─ Claude Code: "你的研究方向是什么？"
│   ├─ 研究员: "EDA，用 AI 做电路设计"
│   ├─ Claude Code: 推荐 topics/keywords/sources → 确认 → 保存
│   └─ Claude Code: "要现在收集一周论文吗？"
├─ /start-my-day
│   ├─ 收集 + 评分 + 推荐
│   └─ "推荐 5 篇，要看哪篇？"
├─ "第 3 篇展开" → 详情 → "要深入分析吗？"
└─ "帮我分析" → 笔记 → "保存到哪？"

Day 2+ — 日常使用（Claude Code）
├─ /start-my-day → 推荐 → 选 → 读 → 分析
├─ "搜索 LoRA" → 结果 → "看哪篇？" → 展开
├─ 写代码时 → "这个 attention 机制有论文吗？"
│   └─ Claude Code 建议搜索 → 调 paper_search
└─ "把刚才的分析保存到 notes/" → 写入文件

Week 2+ — 多篇智能使用（v02）
├─ "搜索 RL chip placement" → paper_search → 不够？
│   └─ paper_search_online 补搜 arXiv
├─ "把这几篇下载一下" → /paper-download → PDF 下载
├─ "做个方法对比" → /paper-compare → 选维度 → 表格 → 分析
├─ "基于这些写 survey" → /paper-survey → 选章节 → 生成草稿
├─ "Background 太短" → 修改 → "保存到 survey/xxx.md"
├─ "导出 BibTeX" → paper_export → refs.bib
├─ 调整 profile: "加上 routing 方向"
│   └─ Claude Code → paper_profile_update
└─ 调整 sources: "开启 cs.PL"
    └─ Claude Code → paper_sources_enable
```

---

## 4. v02 — 多篇智能（已实现）

### 4.1 核心升级：单篇 → 多篇智能

v01 是**单篇论文**的交互（搜索→看一篇→分析一篇）。
v02 升级到**多篇论文**的交互（选多篇→对比→综述→导出）。

### 4.2 新增 MCP Tools（✅ 已实现）

| Tool | 用途 | 交互方式 | 状态 |
|------|------|---------|------|
| `paper_batch_show` | 批量获取多篇论文详情 | 一次返回多篇 JSON | ✅ 已实现 |
| `paper_compare` | 多篇论文对比分析 | Claude Code 问对比维度 → 选择 → 生成 | ✅ 已实现 |
| `paper_export` | 导出 BibTeX / markdown / JSON | Claude Code 问格式/路径 → 导出 | ✅ 已实现 |
| `paper_download` | 下载论文 PDF | Claude Code 批量下载 → 报告路径 | ✅ 已实现 |
| `paper_search_online` | 实时搜索 arXiv API | 补充本地库不足 | ✅ 已实现 |
| `paper_select` | 从搜索结果中多选论文 | MCP Elicitation checkbox UI | 🔲 待 MCP Elicitation 支持 |

### 4.3 新增 Claude Code 命令（✅ 已实现）

| 命令 | 用途 | 交互流程 |
|------|------|---------|
| `/paper-survey <topic>` | 综述 | 搜索 → 选论文 → 选章节 → 生成 → 反馈修改 → 保存 |
| `/paper-compare` | 对比 | 选论文 → 选维度 → 生成表格 → 分析 → 保存 |
| `/paper-download <id>` | 下载 | 下载 → 报告路径 → 问是否阅读 |

### 4.4 v02 完整交互旅程示例

> 一个完整的研究场景：从模糊想法到 survey 成品

```
研究员: "我要写一个关于 AI for EDA placement 的 survey"

── ① 定位 ──
Claude Code:
  "我来帮你分析搜索方向：
   ├─ 关键词: reinforcement learning, chip placement, GNN, floorplanning
   ├─ 相关分类: cs.AR, cs.AI, cs.LG
   └─ 搜索策略: 先搜本地库，不够再搜 arXiv
   这些关键词覆盖够吗？"

研究员: "加上 simulated annealing 和 analytical placement"

Claude Code: "好的，已补充。开始搜索。"

── ② 搜索 ──
Claude Code:
  ├─ [paper_search("RL chip placement GNN SA analytical")] → 本地 12 篇
  ├─ "本地 12 篇，要不要再搜 arXiv 补充？"
研究员: "搜一下"
  ├─ [paper_search_online("AI chip placement optimization")] → 线上 30 篇
  └─ "合并 42 篇候选。要过滤时间范围吗？"
研究员: "只看 2023 以后的"
  └─ 过滤 → 28 篇

── ③ 筛选 ──
Claude Code:
  ├─ 展示 28 篇列表
  └─ [弹出 checkbox UI]
研究员: ✅ 勾选 15 篇
Claude Code: "你选了 15 篇。想先做什么？"
  a) 方法对比  b) 生成 survey  c) 先下载 PDF  d) 导出 BibTeX

── ④ 下载 ──
研究员: "先下载"
Claude Code:
  ├─ [paper_download(15 篇)] → 下载到 papers/
  └─ "✅ 已下载 15 篇 PDF。接下来？"

── ⑤⑥ 阅读 + 分析 ──
研究员: "先快速看看这 15 篇的摘要"
Claude Code:
  ├─ [paper_batch_show(15 篇)]
  ├─ 展示每篇一行摘要
  └─ "要对哪篇深入分析？"
研究员: "第 3 篇看看"
Claude Code: → 结构化分析笔记

── ⑦ 对比 ──
研究员: "做个方法对比"
Claude Code:
  ├─ "从哪些维度对比？" → [选择 UI]
研究员: ✅ 方法架构  ✅ 实验结果
Claude Code:
  ├─ 生成对比表格
  └─ "要基于这些写 survey 吗？"

── ⑧ 综述 ──
研究员: "写 survey"
Claude Code:
  ├─ "包含哪些章节？" → [选择 UI]
研究员: ✅ 全选
Claude Code:
  ├─ 生成 survey 草稿
  └─ "看看？需要修改哪里？"
研究员: "Background 太短"
Claude Code:
  ├─ 补充 → "修改完成，保存到哪？"

── ⑨ 导出 ──
研究员: "保存到 survey/eda-placement.md，顺便导出 BibTeX"
Claude Code:
  ├─ [写入 survey] + [paper_export → refs.bib]
  └─ "✅ 全部完成"
```

---

## 5. 能力分工与交互职责

| 职责 | paper-agent (数据层) | Claude Code (交互层) |
|------|---------------------|---------------------|
| **数据存储** | ✅ SQLite 论文库 | — |
| **论文收集** | ✅ arXiv 抓取 + 去重 | — |
| **LLM 评分** | ✅ 后端 LLM 打分 | — |
| **全文检索** | ✅ FTS5 搜索引擎 | — |
| **Profile 存储** | ✅ topics/keywords/sources | — |
| **理解意图** | — | ✅ 自然语言 → 结构化查询 |
| **引导确认** | — | ✅ 追问、澄清、确认 |
| **格式化呈现** | 返回 JSON | ✅ 中文、表格、wikilink |
| **分析合成** | 提供数据 | ✅ 生成笔记、对比、综述 |
| **文件操作** | — | ✅ 写 markdown/BibTeX |
| **交互 UI** | v02: MCP Elicitation | ✅ 对话 + checkbox + 选择 |
| **流程引导** | — | ✅ 每步结束建议下一步 |

**核心原则**：
- paper-agent 管**数据**（收集、存储、检索、评分）
- Claude Code 管**交互+智能**（理解、确认、分析、合成、呈现、引导下一步）
- **没有环节是"调完 API 就结束的"**，每步都有对话

---

## 6. 能力缺口分析（含交互层）

### 6.1 v01 交互层缺口

| 环节 | 现状 | 缺什么 |
|------|------|-------|
| 定位 | Claude Code 可以做，但没有专用引导 | 需要让 Claude Code 主动分析关键词、扩展搜索词、确认 |
| 筛选 | 用户口头说编号 | v02 需要 checkbox UI (MCP Elicitation) |
| 分析后保存 | Claude Code 可写文件，但不主动问 | 命令模板应引导"分析完问是否保存" |
| 多步流程引导 | 每个命令独立，不串联 | v02 命令应串联（搜→选→比→写→导出） |

### 6.2 v02 实现状态

| 能力 | 优先级 | 状态 | Claude Code 交互职责 |
|------|--------|------|---------------------|
| `paper_batch_show`（批量） | P0 | ✅ 已实现 | 格式化展示 + 总结 |
| `paper_compare`（对比） | P0 | ✅ 已实现 | 问维度 → 生成表格 → 分析总结 |
| `paper_export`（BibTeX/md） | P1 | ✅ 已实现 | 问格式/路径 → 导出 → 确认 |
| `paper_download`（PDF） | P1 | ✅ 已实现 | 批量下载 → 报告 → 问读哪篇 |
| `paper_search_online`（联网） | P2 | ✅ 已实现 | 判断是否补搜 → 追问 → 合并展示 |
| `paper_select`（多选） | P0 | 🔲 待实现 | 弹出 checkbox → 收集选择 (等待 MCP Elicitation) |
| 作者追踪 | P2 | 🔲 v03+ | 提醒 → 展示新论文 |
| 引用网络 | P3 | 🔲 v03+ | 展示引用关系 → 推荐相关论文 |

### 6.3 不需要 paper-agent 实现的（Claude Code 交互层自身能力）

| 能力 | 交互作用 |
|------|---------|
| 搜索意图分析 | 把"我想看 placement 的论文"转化为精确关键词 |
| 关键词扩展与确认 | 主动补充关键词 → 让用户确认 |
| 中文翻译 + 总结 | 把英文摘要转化为中文要点 |
| 笔记生成 + 保存 | 生成 markdown → 问路径 → 写入 |
| 流程引导 | 每步结束建议下一步（"要继续分析吗？""保存吗？"） |
| 对话式修改 | "Background 太短" → 修改 → 再确认 |
| checkbox 多选 | 弹出选择 UI，用户勾选 |

---

## 7. 版本路线图

```
v01 (已实现) — 单篇交互
├─ CLI + MCP Server 基础架构
├─ arXiv 收集 + LLM 过滤 + 每日推荐
├─ 本地搜索 + 单篇分析
├─ Profile 管理（CLI + Claude Code 对话式）
├─ Claude Code 集成 (setup + commands)
├─ 交互覆盖：搜索、阅读、分析、追踪
└─ 交互模式：自然语言 + slash 命令 → AI 调工具 → 呈现 → 追问

v01_source (进行中) — 多源数据
├─ 多源收集 (arXiv + OpenReview + DBLP + ACL Anthology)
├─ Source Registry 管理
└─ Profile 引导增强

v02 (已实现) — 多篇交互
├─ 多篇论文智能
│   ├─ paper_batch_show ✅ 批量展示
│   ├─ paper_compare ✅ 对比（含维度选择交互）
│   ├─ paper_export ✅ BibTeX/markdown/JSON 导出
│   └─ paper_download ✅ PDF 下载
├─ 智能搜索
│   └─ paper_search_online ✅ arXiv API 实时搜索
├─ 串联流程命令
│   ├─ /paper-survey ✅ 综述全流程
│   ├─ /paper-compare ✅ 对比全流程
│   └─ /paper-download ✅ 下载全流程
├─ 待实现
│   └─ paper_select 🔲 MCP Elicitation checkbox（等待协议支持）
└─ 交互模式升级：流程串联 + 反馈修改

v03+ (远期) — 智能追踪与协作
├─ 引用网络探索
├─ 作者追踪与提醒
├─ Semantic Scholar / PapersWithCode 集成
├─ 团队共享论文库
└─ Web UI (可选)
```

---

## 8. 相关文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| v01 需求 | `docs/v01/requirement.md` | 基础需求定义 |
| v01 用户旅程 | `docs/v01/user-journey.md` | CLI + IDE 用户旅程（含交互设计） |
| v01_source 需求 | `docs/v01_source/requirement.md` | 多源扩展需求 |
| v01_source MVP | `docs/v01_source/mvp.md` | 多源 MVP scope |
| README | `README.md` | 安装、使用、IDE 集成指南 |
| Plugin README | `plugin/README.md` | IDE 插件目录说明 |
