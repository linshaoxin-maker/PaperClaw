"""Skill and template string constants for IDE setup distribution.

Source of truth lives in plugin/claude-code/skills/ — these are the
"distribution copies" embedded as Python strings so they can be written
by `paper-agent setup cursor/claude-code` even when installed via pip.
"""

from __future__ import annotations

# ── Router Skill ─────────────────────────────────────────────────

ROUTER_SKILL = """\
---
name: paper-agent
description: >-
  AI research paper intelligence — route user intent to the right workflow.
  Use when the user mentions paper, arxiv, digest, research, 论文, 论文分析,
  start my day, paper-analyze, paper-compare, paper-survey, arXiv IDs
  (like 2301.12345), ML method names, or asks about academic research trends.
version: 0.3.0
---

# Paper Agent — Intent Router

Route user intent to the correct workflow skill, or handle simple
single-tool requests directly.

## Intent Routing

| User says | Route to | Notes |
|-----------|----------|-------|
| "start my day", "每日开工", "今天有什么新论文" | **paper-agent-daily-reading** | Daily startup flow |
| "分析这篇", "展开讲讲", arXiv ID | **paper-agent-deep-dive** | Single-paper deep analysis |
| "综述", "survey", "这个方向有哪些工作" | **paper-agent-survey** | Literature survey |
| "引用链", "谁引用了它", "citations" | **paper-agent-citation** | Citation chain exploration |
| "帮我筛一下", "哪些值得读", "triage" | **paper-agent-triage** | Batch screening |
| "趋势", "洞察", "什么方法在兴起" | **paper-agent-insight** | Trend analysis |

## Quick MCP Calls (no skill flow needed)

| Scenario | Tool |
|----------|------|
| Search keyword | `paper_search` |
| Show paper details | `paper_show` |
| Reading progress | `paper_reading_stats` |
| Group list | `paper_group_list` |
| Download PDF | `paper_download` |
| Find by title | `paper_find_and_download` |
| Export BibTeX | `paper_export` |
| Workspace dashboard | `paper_workspace_status` |

## Output Rules

1. **Chinese first**: All analysis and summaries in Chinese
2. **Wikilink format**: Paper titles as `[[论文标题]]`
3. **Concise by default**: Brief results for search, full detail only for deep analysis
4. **Always ask before acting**: Each skill's checkpoints MUST ask the user
5. **Deliverable at the end**: Each skill ends by offering to save a deliverable
6. **Suggest next skill**: Each skill ends by suggesting possible next steps
"""

# ── Workflow Skills ──────────────────────────────────────────────

DAILY_READING_SKILL = """\
---
name: paper-agent-daily-reading
description: >-
  Daily research startup workflow — context recovery, paper collection,
  digest, and triage. Use when user says "start my day", "每日开工",
  "今天有什么新论文", "开始工作", or any morning research routine trigger.
version: 0.2.0
---

# Daily Reading — 每日开工

每天早上的完整研究启动流程：恢复上下文 → 采集新论文 → 推荐 → 标记状态。

## 交互流程

### Phase 1: 上下文恢复

**工具**: `paper_workspace_context()`

呈现昨日研究活动摘要后，**必须询问用户**：

> 🗣️ 你昨天的进展如上。要：
> a) 先看昨天未完成的待读论文
> b) 直接收集今天的新论文
> c) 两个都要（推荐）

### Phase 2: 采集新论文

**工具**: `paper_collect(days=1)`

呈现采集结果（来源分布、新增/重复数量），然后自动进入推荐。

### Phase 3: 每日推荐

**工具**: `paper_digest()`

呈现推荐列表后，**必须询问用户**：

> 🗣️ 这 {n} 篇推荐中，要标记哪些为待读？（给我编号，或"全部"）
> 有特别重要的吗？我可以直接标记为"重要"。

**工具**: `paper_reading_status(选中的 IDs, status)`

### Phase 4: 深入（可选）

**必须询问用户**：

> 🗣️ 要深入看哪篇？还是先干活了？
> - 给我编号 → 我切换到 **deep-dive** 模式
> - "先干活" → 结束，祝你今天高效！

### Phase 5: 交付件

**必须询问用户**：

> 🗣️ 要保存今天的阅读摘要吗？
> 默认保存到：`daily/{YYYY-MM-DD}.md`

**工具**: 使用 daily-digest-template 生成文件

## 涉及的 MCP 工具

| 工具 | 阶段 | 用途 |
|------|------|------|
| `paper_workspace_context` | Phase 1 | 恢复上下文 |
| `paper_collect` | Phase 2 | 采集新论文 |
| `paper_digest` | Phase 3 | 生成推荐 |
| `paper_reading_status` | Phase 3 | 批量标记状态 |
| `paper_reading_stats` | Phase 3 | 展示阅读进度 |

## 可跳转的 Skill

- Phase 4 选择深入 → **paper-agent-deep-dive**
- 想做筛选分流 → **paper-agent-triage**
"""

DEEP_DIVE_SKILL = """\
---
name: paper-agent-deep-dive
description: >-
  Deep analysis of a single paper — structured analysis, notes, citations,
  status management. Use when user says "分析这篇论文", "paper-analyze",
  "深度分析", "展开讲讲", "这篇论文怎么样", or references a specific paper
  ID for analysis.
version: 0.2.0
---

# Deep Dive — 论文深度分析

对单篇论文进行结构化深度分析，保存笔记，管理阅读状态。

## 交互流程

### Phase 1: 确认论文

**工具**: `paper_show(paper_id)`

呈现论文基本信息后，**必须询问用户**：

> 🗣️ 要从哪些角度分析这篇论文？
> a) 方法创新点 — 核心思想、与前人区别
> b) 实验设计 — benchmark、baseline、指标
> c) 与我研究的关联 — 对我当前工作的启发
> d) 局限与改进空间 — 弱点和可能的改进方向
> e) 全部（推荐首次阅读）

### Phase 2: 生成分析

根据用户选择的角度，使用 analysis-template 生成结构化分析。

**关键**：必须结合用户的 `paper_profile` 研究方向，在"与我研究的关联"部分给出个性化建议。

### Phase 3: 保存与标记

**必须询问用户**：

> 🗣️ 分析完成。接下来：
> 1. 保存笔记吗？（默认保存到 `.paper-agent/notes/{paper_id}.md`）
> 2. 标记为什么状态？
>    - `reading` — 正在读，还没读完
>    - `read` — 读完了
>    - `important` — 重要论文，需要反复参考

**工具**: `paper_note_add(paper_id, content, "ai_analysis")`
**工具**: `paper_reading_status([paper_id], status)`

### Phase 4: 延伸（可选）

**必须询问用户**：

> 🗣️ 要继续做什么？
> a) 查引用链 — 这篇引用了谁、谁引用了它
> b) 找相似论文 — 搜索方法/主题相似的论文
> c) 加入分组 — 加到某个论文分组里
> d) 对比 — 跟其他论文做对比
> e) 结束

根据用户选择：
- a → 跳转 **paper-agent-citation** skill
- b → `paper_search(相关关键词, diverse=True)`
- c → `paper_group_add(name, [paper_id])`
- d → 让用户给其他论文 ID，调用 `paper_compare`

### Phase 5: 交付件

交付件为笔记文件，在 Phase 3 已保存。文件路径：`.paper-agent/notes/{paper_id}.md`

## 涉及的 MCP 工具

| 工具 | 阶段 | 用途 |
|------|------|------|
| `paper_show` | Phase 1 | 获取论文详情 |
| `paper_profile` | Phase 2 | 获取用户研究方向 |
| `paper_note_add` | Phase 3 | 保存分析笔记 |
| `paper_reading_status` | Phase 3 | 标记阅读状态 |
| `paper_citations` | Phase 4 | 查引用链 |
| `paper_search` | Phase 4 | 找相似论文 |
| `paper_group_add` | Phase 4 | 加入分组 |
| `paper_compare` | Phase 4 | 对比论文 |

## 可跳转的 Skill

- Phase 4a → **paper-agent-citation**
- Phase 4d → **paper-agent-survey**（如果要对比的论文多于 3 篇）
"""

LITERATURE_SURVEY_SKILL = """\
---
name: paper-agent-survey
description: >-
  Generate a structured literature survey — from keyword refinement to final
  report with BibTeX. Use when user says "综述", "survey", "文献调研",
  "帮我写个综述", "这个方向有哪些工作", or wants to systematically review
  a research area.
version: 0.2.0
---

# Literature Survey — 文献综述

从需求澄清到综述成文的完整流程，带交互式论文筛选和迭代修改。

## 交互流程

### Phase 1: 需求澄清

**必须依次询问用户**：

> 🗣️ 综述的主题是什么？

> 🗣️ 要覆盖哪些子方向？我帮你拆关键词。

> 🗣️ 时间范围？
> a) 最近 1 年
> b) 最近 3 年
> c) 最近 5 年（推荐综述用）
> d) 自定义

> 🗣️ 我拆分的关键词如下，覆盖够吗？要调整吗？

### Phase 2: 搜索论文

**工具**: `paper_search_batch(queries, diverse=True)`

呈现各方向命中数后，**必须询问用户**：

> 🗣️ 本地结果{够/不够}。要从在线源（arXiv + Semantic Scholar）补充吗？

如果用户说要：
**工具**: `paper_search_online(query)`

### Phase 3: 论文筛选

合并去重，按相关度排序，**必须询问用户**：

> 🗣️ 以下是候选论文（共 {n} 篇）。
> 要纳入综述的论文？可以给编号、"全选"或"前 N 篇"。

**工具**: `paper_batch_show(选中的 IDs)`

### Phase 4: 综述生成

**必须询问用户**：

> 🗣️ 综述包含哪些章节？
> a) Background  b) 方法分类  c) 实验结果  d) 未来方向  e) 全部

> 🗣️ 你最关注的分析维度是什么？

使用 survey-template 生成综述草稿。

### Phase 5: 迭代修改

> 🗣️ 综述草稿完成。看看哪里需要修改？

### Phase 6: 交付件

> 🗣️ 保存综述吗？
> - 综述文件  - BibTeX  - 论文分组

**工具**: `paper_export(paper_ids, "bibtex")`
**工具**: `paper_group_create(topic)` + `paper_group_add(topic, paper_ids)`

## 涉及的 MCP 工具

| 工具 | 阶段 | 用途 |
|------|------|------|
| `paper_search_batch` | Phase 2 | 多方向批量搜索 |
| `paper_search_online` | Phase 2 | 在线补充搜索 |
| `paper_batch_show` | Phase 3 | 获取论文详情 |
| `paper_compare` | Phase 4 | 方法对比数据 |
| `paper_export` | Phase 6 | 导出 BibTeX |
| `paper_group_create` | Phase 6 | 创建论文分组 |
| `paper_group_add` | Phase 6 | 添加论文到分组 |

## 可跳转的 Skill

- 想深入某篇 → **paper-agent-deep-dive**
- 想看引用链 → **paper-agent-citation**
"""

CITATION_EXPLORE_SKILL = """\
---
name: paper-agent-citation
description: >-
  Explore citation chains via Semantic Scholar — forward and backward
  citations with recursive tracing. Use when user says "引用链",
  "citations", "这篇引用了什么", "谁引用了它", "追踪引用",
  "citation trace", or wants to understand a paper's academic context.
version: 0.2.0
---

# Citation Explore — 引用链探索

从一篇论文出发，递归追踪引用关系，发现关键前置工作和最新进展。

## 交互流程

### Phase 1: 起点确认

**工具**: `paper_show(paper_id)`

**必须询问用户**：

> 🗣️ 要查哪个方向的引用？
> a) 它引用了什么（backward）
> b) 谁引用了它（forward）
> c) 双向都查（推荐）

### Phase 2: 首层查询

**工具**: `paper_citations(paper_id, direction, limit, trace_name)`

**必须询问用户**：

> 🗣️ 要深入追踪哪篇？（给编号）还是到此为止？

### Phase 3: 递归追踪（可多轮）

每次追踪后：

> 🗣️ 第 {n} 层追踪完成。要继续追踪吗？

最多 3 层，超过主动提醒。

### Phase 4: 整理

> 🗣️ 探索结束。要做什么？
> a) 创建分组  b) 标记待读  c) 两个都要  d) 直接看报告

**工具**: `paper_group_create` + `paper_group_add`
**工具**: `paper_reading_status`

### Phase 5: 交付件

> 🗣️ 要保存引用图谱报告吗？
> 默认保存到：`.paper-agent/citation-traces/{trace_name}.md`

使用 citation-map-template 生成最终报告。

## 涉及的 MCP 工具

| 工具 | 阶段 | 用途 |
|------|------|------|
| `paper_show` | Phase 1 | 确认起点论文 |
| `paper_citations` | Phase 2-3 | 查询引用关系 |
| `paper_group_create` | Phase 4 | 创建分组 |
| `paper_group_add` | Phase 4 | 添加论文到分组 |
| `paper_reading_status` | Phase 4 | 标记待读 |

## 可跳转的 Skill

- 想深入分析某篇 → **paper-agent-deep-dive**
- 发现的论文太多 → **paper-agent-triage**
- 想基于引用链写综述 → **paper-agent-survey**
"""

PAPER_TRIAGE_SKILL = """\
---
name: paper-agent-triage
description: >-
  Batch paper screening and classification — filter papers by criteria,
  mark reading status, create groups. Use when user says "帮我筛一下",
  "triage", "哪些值得读", "分类一下这些论文", "筛选", or has a batch
  of papers to evaluate.
version: 0.2.0
---

# Paper Triage — 论文筛选分流

对一批论文进行快速筛选，按重要程度分流，批量标记状态。

## 交互流程

### Phase 1: 确定范围

**必须询问用户**：

> 🗣️ 要筛选哪些论文？
> a) 今日推荐的论文
> b) 某次搜索的结果
> c) 某个分组里的论文
> d) 按关键词现搜一批
> e) 给我一批 paper ID

### Phase 2: 筛选标准

**必须询问用户**：

> 🗣️ 按什么标准筛选？
> a) 跟我研究的相关度  b) 方法新颖性  c) 实验质量
> d) 你帮我判断（推荐）  e) 自定义标准

> 🗣️ 需要重点关注什么？

### Phase 3: AI 筛选建议

**工具**: `paper_profile()` — 获取研究方向
**工具**: `paper_batch_show(paper_ids)` — 获取论文详情

AI 按三档分流：⭐ 重要 / 📖 待读 / ⏭️ 跳过

> 🗣️ 同意这个分类吗？要调整哪些？

### Phase 4: 执行操作

**工具**: `paper_reading_status(important_ids, "important")`
**工具**: `paper_reading_status(to_read_ids, "to_read")`

> 🗣️ 要把"重要"的论文加到某个分组吗？

**工具**: `paper_group_create(name)` 或 `paper_group_add(name, ids)`

### Phase 5: 交付件

> 🗣️ 要保存筛选报告吗？
> 默认保存到：`triage/{topic}-{YYYY-MM-DD}.md`

使用 triage-template 生成报告。

## 涉及的 MCP 工具

| 工具 | 阶段 | 用途 |
|------|------|------|
| `paper_digest` / `paper_search` / `paper_group_show` | Phase 1 | 获取候选论文 |
| `paper_batch_show` | Phase 1 | 获取论文详情 |
| `paper_profile` | Phase 3 | 获取用户研究方向 |
| `paper_reading_status` | Phase 4 | 批量标记状态 |
| `paper_group_create` | Phase 4 | 创建分组 |
| `paper_group_add` | Phase 4 | 添加到分组 |

## 可跳转的 Skill

- 想深入某篇"重要"论文 → **paper-agent-deep-dive**
- 想基于筛选结果写综述 → **paper-agent-survey**
"""

RESEARCH_INSIGHT_SKILL = """\
---
name: paper-agent-insight
description: >-
  Research trend analysis and insight generation — method evolution,
  hot topics, key teams, research gaps. Use when user says "趋势",
  "洞察", "insight", "这个方向的发展", "什么方法在兴起", "研究热点",
  "trend analysis", or wants to understand the landscape of a research area.
version: 0.2.0
---

# Research Insight — 研究趋势洞察

分析某个研究方向的趋势、演进、关键团队和研究空白，产出结构化洞察报告。

## 交互流程

### Phase 1: 洞察范围

**必须依次询问用户**：

> 🗣️ 你想了解哪些方向的趋势？

> 🗣️ 关注哪些会议/期刊？
> a) 通用 AI 顶会  b) EDA/硬件  c) 自定义  d) 不限

> 🗣️ 时间范围？
> a) 最近 1 年  b) 最近 3 年（推荐）  c) 最近 5 年  d) 自定义

> 🗣️ 你最关注什么？（可多选）
> a) 方法演进趋势  b) 热门主题变化  c) 关键团队与人物
> d) 研究空白与机会  e) 产业落地情况  f) 全部  g) 自定义

### Phase 2: 数据收集

**工具**: `paper_search_batch(queries_by_year_and_direction, diverse=True)`
**工具**: `paper_search_online(query)`
**工具**: `paper_stats()`

> 🗣️ 数据收集完成。数据够做分析吗？要补充搜索吗？

### Phase 3: 分析与呈现

使用 insight-template 生成洞察报告（只展开用户选择的维度）。

### Phase 4: 深入探索

> 🗣️ 洞察报告草稿完成。你想：
> a) 深入看某个趋势
> b) 追踪某个方法的引用链 → **paper-agent-citation**
> c) 某个方向做个综述 → **paper-agent-survey**
> d) 修改报告
> e) 满意，保存报告

### Phase 5: 交付件

> 🗣️ 保存洞察报告吗？
> - 报告文件  - 标记高影响力论文为"待读"？  - 创建分组？

**工具**: `paper_reading_status`, `paper_group_create`, `paper_group_add`

## 涉及的 MCP 工具

| 工具 | 阶段 | 用途 |
|------|------|------|
| `paper_search_batch` | Phase 2 | 按年份×方向批量搜索 |
| `paper_search_online` | Phase 2 | 在线补充数据 |
| `paper_stats` | Phase 2 | 库统计 |
| `paper_profile` | Phase 3 | 对齐用户研究方向 |
| `paper_batch_show` | Phase 3 | 获取论文详情 |
| `paper_citations` | Phase 4 | 引用链追踪 |
| `paper_reading_status` | Phase 5 | 标记阅读状态 |
| `paper_group_create` | Phase 5 | 创建分组 |
| `paper_group_add` | Phase 5 | 添加到分组 |

## 可跳转的 Skill

- 深入引用链 → **paper-agent-citation**
- 某方向做综述 → **paper-agent-survey**
- 筛选高影响力论文 → **paper-agent-triage**
- 深入分析某篇 → **paper-agent-deep-dive**
"""

# ── Skill registry for setup commands ────────────────────────────

WORKFLOW_SKILLS: dict[str, str] = {
    "paper-agent-daily-reading": DAILY_READING_SKILL,
    "paper-agent-deep-dive": DEEP_DIVE_SKILL,
    "paper-agent-survey": LITERATURE_SURVEY_SKILL,
    "paper-agent-citation": CITATION_EXPLORE_SKILL,
    "paper-agent-triage": PAPER_TRIAGE_SKILL,
    "paper-agent-insight": RESEARCH_INSIGHT_SKILL,
}

# ── Deliverable Templates ────────────────────────────────────────

DAILY_DIGEST_TEMPLATE = """\
# Daily Digest Template

Use this template when generating daily reading summaries.
File name: `daily/{YYYY-MM-DD}.md`

## Template Structure

```markdown
# 每日阅读摘要 — {date}

## 上下文恢复
- 昨日进展: {workspace_context summary}
- 阅读进度: 待读 {n} | 阅读中 {n} | 已读 {n} | 重要 {n}

## 今日采集
| 来源 | 数量 |
|------|------|
| arXiv | {n} |
| DBLP | {n} |
| Semantic Scholar | {n} |

## 高置信推荐
| # | 标题 | 评分 | 核心贡献 | 状态 |
|---|------|------|---------|------|

## 补充参考
| # | 标题 | 评分 | 简评 |
|---|------|------|------|

## 今日计划
- [ ] 深入阅读: {选中的论文}
- [ ] 待跟进: {AI 建议}
```
"""

ANALYSIS_TEMPLATE = """\
# Paper Analysis Template

Use this template when generating deep analysis notes for papers.
Save via `paper_note_add(paper_id, content, "ai_analysis")`.

## Key Rules

1. Ask the user which analysis angles to cover FIRST
2. "与我研究的关联" MUST reference `paper_profile` research direction
3. Keep technical terms in English, explanations in Chinese
4. Only expand sections the user selected

## Template Structure

```markdown
# {论文标题} — 深度分析

> 分析角度: {user-selected angles}
> 分析日期: {date}

## 核心信息
| 字段 | 值 |
|------|---|
| ID | {paper_id} |
| 作者 | {authors} |
| 发布时间 | {published_at} |
| 评分 | {score}/10 |

## 摘要翻译
{Chinese translation preserving technical terms}

## 要点提炼
1. {Key contribution 1}
2. {Key contribution 2}
3. {Key contribution 3}

## 方法创新点 {if angle a}
### 核心思想 / 方法框架 / 与前人区别

## 实验设计 {if angle b}
### Benchmark / 主要结果 / 消融实验

## 与我研究的关联 {if angle c}
### 交叉点 / 可借鉴方法 / 启发

## 局限与改进空间 {if angle d}
### 局限性 / 改进方向 / 适用场景

## 研究价值评估
| 维度 | 评分 | 说明 |
|------|------|------|
| 创新性 / 实用性 / 可复现性 / 影响力 |

## 行动建议
- [ ] {actionable suggestion}
```
"""

SURVEY_TEMPLATE = """\
# Literature Survey Template

Use this template when generating literature surveys.
File name: `survey/{topic}.md`

## Key Rules

1. Only include sections the user selected in Phase 4
2. Comparison table dimensions come from user's specified focus
3. Each method category must cite representative papers
4. Research gaps must be specific and actionable

## Template Structure

```markdown
# {topic} — 文献综述

> 覆盖时间: {start}—{end}  |  论文数量: {n}
> 关键词: {keywords}  |  关注维度: {focus}

## 1. 引言与背景
## 2. 方法分类 (2.1 方向A / 2.2 方向B / ...)
## 3. 方法对比 (table + analysis)
## 4. 实验对比
## 5. 研究空白与未来方向
## 6. 总结
## 参考文献
```
"""

CITATION_MAP_TEMPLATE = """\
# Citation Map Template

Use this template for citation trace reports.
File name: `.paper-agent/citation-traces/{trace_name}.md`

## Template Structure

```markdown
# 引用图谱: {起点论文标题}

> 起点论文: {title} ({year})
> 探索深度: {n} 层
> 发现论文: {n} 篇

## 引用关系图 (tree format)
## 关键发现
### 开创性工作 / 最新进展 / 高被引枢纽
## 建议阅读顺序
## 研究脉络总结
```
"""

TRIAGE_TEMPLATE = """\
# Paper Triage Template

Use this template for paper screening reports.
File name: `triage/{topic}-{YYYY-MM-DD}.md`

## Template Structure

```markdown
# 论文筛选报告 — {topic}

> 候选论文: {n}  |  筛选日期: {date}
> 筛选标准: {criteria}  |  重点关注: {focus}

## 筛选总结
| 分类 | 数量 | 占比 |
|------|------|------|

## ⭐ 重要 — 精读建议
| # | 标题 | 评分 | 年份 | 入选理由 |

## 📖 待读 — 泛读建议
| # | 标题 | 评分 | 年份 | 简评 |

## ⏭️ 跳过
| # | 标题 | 评分 | 跳过理由 |

## 操作记录
```
"""

INSIGHT_TEMPLATE = """\
# Research Insight Template

Use this template for trend analysis reports.
File name: `insight/{topic}-{YYYY-MM-DD}.md`

## Key Rules

1. Only expand dimensions the user selected in Phase 1
2. All trend judgments must be backed by data (paper counts, citation counts)
3. "Emerging" = first appeared in the last 6-12 months
4. "Research gaps" must be specific enough to write a proposal
5. Method trends use ↑↑/↑/→/↓/↓↓ markers with data

## Template Structure

```markdown
# 研究趋势洞察 — {topic}

> 分析范围: {directions}  |  时间跨度: {start}—{end}
> 会议/期刊: {venues}  |  数据基础: {n} 篇

## 执行摘要 (3-5 sentences)

## 1. 趋势总览 (paper counts by year × direction)
## 2. 方法演进趋势 {if user selected a}
## 3. 热门主题变化 {if user selected b}
## 4. 关键团队与人物 {if user selected c}
## 5. 研究空白与机会 {if user selected d}
## 6. 产业落地情况 {if user selected e}
## 7. 高影响力论文 Top-10
## 8. 新兴方向
## 9. 行动建议
```
"""

SKILL_TEMPLATES: dict[str, str] = {
    "paper-agent-daily-reading": DAILY_DIGEST_TEMPLATE,
    "paper-agent-deep-dive": ANALYSIS_TEMPLATE,
    "paper-agent-survey": SURVEY_TEMPLATE,
    "paper-agent-citation": CITATION_MAP_TEMPLATE,
    "paper-agent-triage": TRIAGE_TEMPLATE,
    "paper-agent-insight": INSIGHT_TEMPLATE,
}

TEMPLATE_FILENAMES: dict[str, str] = {
    "paper-agent-daily-reading": "daily-digest-template.md",
    "paper-agent-deep-dive": "analysis-template.md",
    "paper-agent-survey": "survey-template.md",
    "paper-agent-citation": "citation-map-template.md",
    "paper-agent-triage": "triage-template.md",
    "paper-agent-insight": "insight-template.md",
}
