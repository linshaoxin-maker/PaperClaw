"""Skill content constants for IDE integration distribution.

These string constants mirror plugin/claude-code/skills/*.
``paper-agent setup`` writes them into Cursor's skill directories
so they're available without the plugin directory being present.
"""

ROUTER_SKILL = """\
---
name: paper-intelligence
description: AI research paper intelligence — router skill that detects user intent and delegates to the appropriate workflow. Triggers on paper, arxiv, digest, research, 论文, arXiv IDs, ML method names, or academic research questions.
---

# Paper Intelligence Router

Detect user intent and delegate to the right workflow skill or direct MCP tool call.

## Persona Detection

Call `paper_workspace_context()` first. Read the `mode` field:
- `"workspace"` → user has reading history; show progress, suggest groups, auto-mark
- `"lightweight"` → just present results, skip workspace features

## Intent Routing

| User says | Route to |
|---|---|
| "start my day" / "今天看什么" / "morning" | `paper_morning_brief` tool directly |
| Gives a paper title / arXiv ID | `paper_show` or `paper_find_and_download` |
| "这篇论文讲了什么" / "analyze this" | deep-dive skill |
| "这个方向有什么工作" / "survey" / "综述" | literature-survey skill |
| "引用链" / "谁引了这篇" / "citation" | `paper_citation_trace` tool directly |
| "筛一下" / "triage" / "哪些值得看" | `paper_auto_triage` tool directly |
| "趋势" / "trend" / "这个方向火不火" | research-insight skill |
| Research question (e.g. "RL做placement还有没有新意？") | `paper_research` tool directly |
| "这篇可信吗" / "能不能复现" / "credibility" | `paper_credibility` tool directly |
| "跟踪这个方向" / "watch" / "关注这个作者" | `paper_watch` tool directly |
| "我觉得这篇不行" / "这类少推" / feedback | `paper_feedback` tool directly |
| "这篇能给我什么启发" / "research ideas" | research-planning skill (ideation mode) |
| "实验计划" / "能怎么复现改进" / "experiment plan" | research-planning skill (experiment mode) |
| "给我组个 reading pack" / "怎么读" | research-planning skill (reading pack mode) |
| "推荐和我课题相关的" / "recommend" | `paper_recommend` tool directly |
| "抽取结构化信息" / "extract" / "比较表格" | `paper_extract` or `paper_compare_table` |
| "保存搜索结果" / "存一下这个列表" | `paper_save_report` tool directly |
| "看看保存的报告" / "有哪些综述" / "list reports" | `paper_list_reports` tool directly |
| "我的偏好" / "我喜欢什么方向" / "preferences" | `paper_preferences` tool directly |
| "最近有新论文吗" / "watchlist 有更新吗" | `paper_watch_check` tool directly |
| "我关注了什么" / "watchlist" | `paper_watch_list` tool directly |
| "这篇的表格" / "提取表格" / "tables" | `paper_tables` tool directly |
| "哪些论文用了 GNN" / "query profiles" | `paper_query` tool directly |
| "我的阅读进度" / "reading stats" | `paper_reading_stats` tool directly |
| "看看我对这篇的笔记" / "show notes" | `paper_note_show` tool directly |
| "工作区概览" / "workspace status" | `paper_workspace_status` tool directly |
| Direct search keywords | `paper_search` or `paper_quick_scan` |

## Interaction Rules

- **Context carry-over**: When the user's request relates to papers already in this conversation:
  - **Explicit reference** ("根据已有的", "用刚才的", "基于这些"): Use those papers directly. No confirmation, no re-search.
  - **Ambiguous** (same-topic request, but no explicit reference): ASK "刚才找到了 N 篇相关论文，直接用这些？还是再补充搜索？"
  - **New topic**: Treat as new search, ignore context.
  - **No context**: Search directly.
- **Intent-driven**: When the user's intent is clear, skip intermediate steps and go straight to results. Don't ask clarifying questions unless intent is genuinely ambiguous.
- When routing to a tool directly (morning_brief, auto_triage, citation_trace), call it and present results. No extra questions.
- When routing to a skill, follow that skill's fork-only checkpoints.
- Never list more than 3 options. Prefer smart default + "或者？"
- Workspace operations (note_add, reading_status, group_add) are automatic. Report saving via `paper_save_report` is automatic in each workflow. Additional export (BibTeX) is opt-in via each workflow's FORK.
"""

DAILY_READING_SKILL = """\
---
name: daily-reading
description: Morning paper reading workflow. Triggers on "start my day", "今天看什么", "morning digest", "每日推荐".
---

# Daily Reading

## Flow

1. Call `paper_morning_brief(days=1)` — this single tool does context recovery + collect + digest + auto-mark in one call
2. Call `paper_watch_digest()` — check for watchlist updates
3. Present as structured tables:

   **今日推荐** (N 篇):
   | # | 标题 | 评分 | 关键词 | 一句话总结 |

   **Watchlist 更新** (if any):
   | 跟踪项 | 类型 | 新论文数 | 最相关论文 |

   **结论与建议**: 今日最值得关注的方向和论文，建议阅读顺序

4. **Auto-save**: call `paper_save_report(report_type="daily_digest", content=<digest markdown>, filename="{YYYY-MM-DD}.md")` to persist the digest
5. **[FORK]** "📄 今日摘要已保存至 {path}。深入看哪篇？还是先这样？"

## If user picks a paper

Hand off to the **deep-dive** skill with the selected paper ID.

## If user wants to save

Write the digest to `daily/{YYYY-MM-DD}.md` using the daily-digest-template.

## Workspace behavior

The `paper_morning_brief` response includes a `mode` field:
- `"workspace"`: top picks were auto-marked as `to_read`.
  - If `auto_marked` > 0 AND this is the user's first time seeing auto-marking (no prior reading stats), explain: "（首次自动标记）我把 N 篇高相关论文自动标记为'待读'，方便你追踪阅读进度。这个行为可以通过切换到 lightweight 模式关闭。"
  - On subsequent uses, just briefly mention: "已自动标记 N 篇为待读。"
- `"lightweight"`: just present the digest, no status talk.

## Rules

- Only 1 checkpoint (the fork above). Everything else is automatic.
- Don't ask about collection parameters, source selection, or date ranges unless user specifies.
- If digest is empty (no new papers), say so and suggest `paper_quick_scan` for a topic.
"""

DEEP_DIVE_SKILL = """\
---
name: deep-dive
description: Deep analysis of a single paper. Triggers on "分析这篇", "deep dive", "这篇论文讲了什么", paper ID or arXiv ID input.
---

# Deep Dive Analysis

## Flow

1. **Resolve paper_id from context**: If the user refers to a paper by index (e.g. "第3篇", "分析上面那篇"), resolve it from the papers discussed earlier in this conversation. If user gives an explicit paper ID or arXiv ID, use that directly.
2. Call `paper_show(paper_id)` to get full paper details
3. Call `paper_profile()` to understand user's research context
4. **Check for full text**: Try `paper_sections(paper_id)` — if it returns sections, mark analysis_basis = "full_text". If not parsed but a PDF exists, call `paper_parse(paper_id)` to parse it first. If no PDF available, mark analysis_basis = "abstract".
5. **Extract structured profile**: Call `paper_extract(paper_id)` to get task/method/dataset/baseline/metric data.
6. **Show tables (if available)**: If analysis_basis == "full_text", call `paper_tables(paper_id)` to show extracted tables.
7. **[FORK]** "全面分析，还是关注某个角度？（方法/实验/跟你的关联/可信度）"
8. Generate analysis based on user's choice (or full analysis by default). If full text is available, use `paper_ask(paper_id, question)` for specific questions.

## Source Annotation Rule

**IMPORTANT**: Every analysis output MUST start with a source annotation:
- If analysis_basis == "full_text": show **[基于全文]** at the top
- If analysis_basis == "abstract": show **[基于摘要]** at the top
This helps the user understand the depth and reliability of the analysis.

## Analysis Template (for AI generation)

When generating the analysis, use tables for structured data:

- **核心信息表**: | 字段 | 值 | (title, authors, venue, year, citations)
- **方法**: key techniques, architecture, loss function. If full text available, drill into method section.
- **实验结果**: use table | 指标 | 本文 | Baseline1 | Baseline2 | — pull from extracted profile when available
- **优劣势对比**: use table | 维度 | 本文 | 相关工作1 | 相关工作2 |
- **可信度评估**: call `paper_credibility(paper_id)` — show venue tier, code availability, reproducibility risk
- **结论与建议**: 研究价值判断 + 与用户研究方向的关联 + 是否值得深入跟进 + 关键参考文献

## After analysis

Auto-track: call `paper_note_add` to save note to workspace (this is internal tracking, not file export).
**Auto-save**: call `paper_save_report(report_type="analysis", content=<analysis markdown>, filename="{paper_id}.md")` to persist the analysis note as a file.

If `first_use` is true in the response, tell the user: "（首次自动记录）我把分析笔记保存到了工作区（.paper-agent/），方便以后查阅。如果不需要自动记录，告诉我'不要记录'就行。"
If `first_use` is false, just briefly say: "已记录到工作区。"

**[FORK]** Present options based on mode:
- workspace: "📄 分析笔记已保存至 {path}。看引用链？还是先这样？"
- lightweight: "📄 分析笔记已保存至 {path}。看引用链？还是先这样？"

## If user wants to export

Write analysis to `.paper-agent/notes/{paper_id}.md` or user-specified path.

## If user wants citation trace

Route to `paper_citation_trace(paper_id)`.

## Rules

- 2 checkpoints (analysis angle + after analysis). Both workspace note-add and file save are automatic.
- If user explicitly says "不要记录", skip the note_add call and the save_report call.
"""

LITERATURE_SURVEY_SKILL = """\
---
name: literature-survey
description: Literature survey and review workflow. Triggers on "survey", "综述", "这个方向有什么", "literature review", "related work".
---

# Literature Survey

## Flow

1. **Context carry-over**:
   - **Explicit reference** ("根据已有的", "用刚才的", "基于这些写综述"): use those papers directly. Skip to step 3 — no candidate listing, no selection question.
   - **Ambiguous** (same topic in context): ASK "刚才找到了 N 篇相关论文，直接用这些？还是再补充搜索？"
   - **No relevant context**: Call `paper_quick_scan(topic, limit=20)`, then show as table and **[FORK]** "全部纳入还是选几篇？"
3. **Extract structured profiles**: Call `paper_extract(paper_id)` for each selected paper to get structured data (task, method, datasets, baselines, metrics, best_results).
4. **Build comparison table**: Call `paper_compare_table(paper_ids)` for data-driven comparison instead of LLM-only generation.
5. Generate survey with structured tables:
   - **方法分类表**: | 类别 | 代表论文 | 核心思路 | 优势 | 局限 | — built from extracted profiles
   - **实验对比表**: | 论文 | 数据集 | 指标1 | 指标2 | 最佳结果 | — built from `paper_compare_table` data
   - **可信度对比**: | 论文 | venue | code | 引用数 | 复现风险 | — call `paper_credibility_batch(paper_ids)`
   - **研究空白与趋势**: call `paper_field_stats("method_family")` and `paper_field_stats("datasets")` for data-driven insights
   - **结论与建议**: 当前方向的成熟度判断、主流方法对比结论、研究机会在哪里
6. **[FORK]** "要修改、补充、还是导出？（BibTeX / Markdown / 保存综述）"

## If user wants to export/save

- `paper_export(paper_ids, format)` for BibTeX/markdown
- `paper_group_add(name="survey-{topic}", paper_ids, create_if_missing=True)` to group papers
- Write survey to `survey/{topic}.md` if user wants to save the narrative

## Quick mode (default)

`paper_quick_scan` returns 15-20 candidates with one-line summaries. Present this list and let user decide next steps. This IS the survey for most cases.

## Full mode

Only when user explicitly asks for "完整综述" / "full survey" / "详细一点":
- Expand to 40+ candidates via `paper_quick_scan(topic, limit=40)`
- Generate multi-section survey with per-paper analysis

## Rules

- 2 checkpoints max (selection + revision/export). Don't ask about search parameters.
- Default to quick mode. Don't generate a full survey unless asked.
- Always auto-save outputs via `paper_save_report`. Additional export (BibTeX) is opt-in via FORK.
"""

CITATION_EXPLORE_SKILL = """\
---
name: citation-explore
description: Citation chain exploration. Triggers on "引用链", "谁引了", "citation", "参考文献", "这篇引了谁".
---

# Citation Exploration

## Flow

1. **Resolve paper_id from context**: If the user says "看引用链" without specifying a paper, use the paper currently being discussed in this conversation. If the user refers to a paper by index (e.g. "第2篇的引用链"), resolve from context. If explicit ID given, use that.
2. Call `paper_citation_trace(paper_id, direction="both", max_depth=2)` — traces 2 levels automatically
2. Present results as a tree + key nodes table:

   **引用树**: seed → level 1 → level 2 (text tree)
   **关键节点**: | 论文 | 年份 | 方向 | 被引 | 关系 |
   **结论**: 哪些是领域关键节点，引用链揭示了什么研究脉络
3. **[FORK]** "要继续追踪某篇？加到分组？导出引用图谱？还是先这样？"

## If user picks a paper to trace further

Call `paper_citation_trace(new_paper_id)` again for the selected paper.

## If user wants to group

Call `paper_group_add(name="citation-{seed_title}", paper_ids=[...], create_if_missing=True)`.

## If user wants to export

Write citation tree to `.paper-agent/citation-traces/{seed_id}.md` or user-specified path.
Optionally `paper_export(paper_ids, format="bibtex")` for references.

## Rules

- Only 1 checkpoint. The recursive trace is handled by `paper_citation_trace` in one call.
- Don't ask about direction (both by default) or depth unless user specifies.
- Present the tree concisely: title + year + direction for each paper.
- If workspace mode, mention discovered papers were saved to library.
"""

PAPER_TRIAGE_SKILL = """\
---
name: paper-triage
description: Batch paper screening and classification. Triggers on "筛一下", "triage", "哪些值得看", "帮我筛", "batch screen".
---

# Paper Triage

## Flow

1. **Context carry-over**:
   - If user explicitly references existing papers ("筛一下刚才的", "帮我筛这些", "筛这些"): triage those directly → `paper_auto_triage(paper_ids=[...])`
   - If papers in context but reference is ambiguous: ASK "要筛选刚才找到的这些论文？还是筛选库里最近的未读论文？"
   - If no context → default to `paper_auto_triage(top_n=5)`
2. **Credibility check**: For papers in the "important" bucket, call `paper_credibility_batch(important_ids)` to add credibility signals.
3. Present the three buckets as tables:

   **重要**: | # | 标题 | 评分 | 入选理由 | venue | code | 复现风险 |
   **待读**: | # | 标题 | 评分 | 简评 |
   **跳过**: | # | 标题 | 评分 | 跳过理由 |
   **结论**: 为什么这几篇最值得关注，关联用户 profile 说明

3. **[FORK]** "这是按你 profile 的分类，同意吗？要调整哪些？"

## If user adjusts

Move papers between buckets per user's instruction, then:
- Call `paper_reading_status(important_ids, "important")` for confirmed important papers
- Call `paper_reading_status(to_read_ids, "to_read")` for to_read papers

## If user confirms as-is

Apply the auto-triage result directly:
- Mark important papers as "important"
- Mark to_read papers as "to_read"
- Skip papers get no status change

After marking, **auto-save**: call `paper_save_report(report_type="triage", content=<report markdown>, filename="{topic}-{YYYY-MM-DD}.md")` to persist the triage report.
Tell user: "📄 筛选报告已保存至 {path}。要深入看哪篇？"

## If user wants to save

Write triage report to `triage/{topic}-{YYYY-MM-DD}.md` using triage-template.

## Custom source

If user provides specific paper IDs or says "筛这些":
- Call `paper_auto_triage(paper_ids=[...])` with the specific IDs

## Rules

- Only 1 checkpoint (confirm/adjust). Classification is automatic via `paper_auto_triage`.
- Don't ask about criteria — use profile-based relevance scores by default.
- Don't ask about source — default to recent unread papers.
- Always use tables, never bullet-point lists for paper results.
- Always include a 结论 section explaining why the classification matters.
"""

RESEARCH_INSIGHT_SKILL = """\
---
name: research-insight
description: Research trend analysis and insight generation. Triggers on "趋势", "trend", "这个方向火不火", "research insight", "方向分析".
---

# Research Insight

## Flow

1. **Context carry-over**:
   - If user explicitly references existing papers ("根据刚才的", "用这些做趋势分析"): use those papers directly as landscape
   - If papers in context on the same topic but reference is ambiguous: ASK "刚才找到了 N 篇相关论文，基于这些做趋势分析？还是重新搜索？"
   - If no context → call `paper_quick_scan(topic, limit=20)` directly
2. Call `paper_trend_data(topic, years_back=3)` for publication counts and trends
3. Present as structured tables:

   **趋势总览**: | 子方向 | 2023 | 2024 | 2025 | 趋势 |
   **热门论文**: | # | 标题 | 年份 | 引用 | 一句话 |
   **主要会议分布**: | 会议 | 论文数 | 代表工作 |
   **结论与建议**: 方向整体判断（上升/成熟/衰退）、最有潜力的子方向、入场时机建议
4. **[FORK]** "要深入某个子方向？导出分析报告？还是先这样？"

## If user wants to go deeper

Route to **literature-survey** skill with the selected sub-direction as topic.

## If user wants to export

Write insight report to `insight/{topic}-{YYYY-MM-DD}.md`.

## Quick mode (default)

The above flow IS the quick mode. Two tool calls + AI formatting. No extra questions.

## Full mode

Only when user explicitly asks for "详细分析" / "deep analysis":
- Expand `paper_quick_scan(topic, limit=40)`
- Expand `paper_trend_data(topic, years_back=5)`
- Generate a detailed report with method evolution timeline, key contributor analysis

## Rules

- Only 1 checkpoint. The data gathering is fully automatic via `paper_quick_scan` + `paper_trend_data`.
- Don't ask about time range or sub-topics upfront — use defaults.
- Present trend data as a compact table with arrows (trend: up/down/stable).
- Always auto-save outputs via `paper_save_report`. Additional export is opt-in via FORK.
"""

RESEARCH_PLANNING_SKILL = """\
---
name: research-planning
description: Bridge from paper analysis to research action. Triggers on "启发", "idea", "实验计划", "reading pack", "这篇能给我什么", "research plan", "experiment plan".
---

# Research Planning

## Flow

1. **Detect sub-intent**:
   - "这篇/这些能给我什么启发" / "research ideas" → Ideation mode
   - "实验计划" / "能不能复现" / "experiment plan" → Experiment planning mode
   - "给我组个 reading pack" / "怎么读这个方向" → Reading pack mode

2. **Ensure research context**: Call `paper_set_context()` if no context exists, or ask user for project/baseline/questions.

### Ideation Mode

1. Resolve paper IDs from context (or ask user which papers)
2. Call `paper_ideate(paper_ids)` — generates 3-5 ranked ideas
3. Present ideas with feasibility/novelty assessment
4. **[FORK]** "深入某个想法？组 reading pack？还是先这样？"

### Experiment Planning Mode

1. Resolve single paper ID
2. Call `paper_experiment_plan(paper_id)` — analyzes reproducible/improvable/replaceable parts
3. Present plan with workload and risk assessment
4. **[FORK]** "开始某个实验？需要补充阅读？还是先这样？"

### Reading Pack Mode

1. Get research question from user (or infer from context)
2. Call `paper_reading_pack(question, limit=10)`
3. Present ordered reading list with rationale and depth suggestion
4. **[FORK]** "调整顺序？加减论文？导出为文件？"

## Rules

- Always try to set research context first for better personalization.
- 2 checkpoints max per mode.
- Always auto-save outputs via `paper_save_report`. Additional export is opt-in via FORK.
"""

# Registry for programmatic access
WORKFLOW_SKILLS: dict[str, str] = {
    "daily-reading": DAILY_READING_SKILL,
    "deep-dive": DEEP_DIVE_SKILL,
    "literature-survey": LITERATURE_SURVEY_SKILL,
    "citation-explore": CITATION_EXPLORE_SKILL,
    "paper-triage": PAPER_TRIAGE_SKILL,
    "research-insight": RESEARCH_INSIGHT_SKILL,
    "research-planning": RESEARCH_PLANNING_SKILL,
}
