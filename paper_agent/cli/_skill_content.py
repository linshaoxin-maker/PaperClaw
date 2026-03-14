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
| Direct search keywords | `paper_search` or `paper_quick_scan` |

## Interaction Rules

- When routing to a tool directly (morning_brief, auto_triage, citation_trace), call it and present results. No extra questions.
- When routing to a skill, follow that skill's fork-only checkpoints.
- Never list more than 3 options. Prefer smart default + "或者？"
- Workspace operations (note_add, reading_status, group_add) are automatic. File export is opt-in via each workflow's FORK.
"""

DAILY_READING_SKILL = """\
---
name: daily-reading
description: Morning paper reading workflow. Triggers on "start my day", "今天看什么", "morning digest", "每日推荐".
---

# Daily Reading

## Flow

1. Call `paper_morning_brief(days=1)` — this single tool does context recovery + collect + digest + auto-mark in one call
2. Present as structured table:

   **今日推荐** (N 篇):
   | # | 标题 | 评分 | 关键词 | 一句话总结 |
   **结论与建议**: 今日最值得关注的方向和论文，建议阅读顺序

3. **[FORK]** "深入看哪篇？保存今日摘要？还是先这样？"

## If user picks a paper

Hand off to the **deep-dive** skill with the selected paper ID.

## If user wants to save

Write the digest to `daily/{YYYY-MM-DD}.md` using the daily-digest-template.

## Workspace behavior

The `paper_morning_brief` response includes a `mode` field:
- `"workspace"`: top picks were auto-marked as `to_read`. Mention this.
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

1. Call `paper_show(paper_id)` to get full paper details
2. Call `paper_profile()` to understand user's research context
3. **[FORK]** "全面分析，还是关注某个角度？（方法/实验/跟你的关联）"
4. Generate analysis based on user's choice (or full analysis by default)

## Analysis Template (for AI generation)

When generating the analysis, use tables for structured data:

- **核心信息表**: | 字段 | 值 | (title, authors, venue, year, citations)
- **方法**: key techniques, architecture, loss function
- **实验结果**: use table | 指标 | 本文 | Baseline1 | Baseline2 |
- **优劣势对比**: use table | 维度 | 本文 | 相关工作1 | 相关工作2 |
- **结论与建议**: 研究价值判断 + 与用户研究方向的关联 + 是否值得深入跟进 + 关键参考文献

## After analysis

Auto-track: call `paper_note_add` to save note to workspace (this is internal tracking, not file export).

**[FORK]** Present options based on mode:
- workspace: "已自动记录到工作区。要导出分析笔记为文件？看引用链？还是先这样？"
- lightweight: "要导出分析笔记为文件？看引用链？还是先这样？"

## If user wants to export

Write analysis to `.paper-agent/notes/{paper_id}.md` or user-specified path.

## If user wants citation trace

Route to `paper_citation_trace(paper_id)`.

## Rules

- 2 checkpoints (analysis angle + after analysis). Workspace note-add is automatic, file export is opt-in.
- If user explicitly says "不要记录", skip the note_add call.
"""

LITERATURE_SURVEY_SKILL = """\
---
name: literature-survey
description: Literature survey and review workflow. Triggers on "survey", "综述", "这个方向有什么", "literature review", "related work".
---

# Literature Survey

## Flow

1. Call `paper_quick_scan(topic, limit=20)` — searches local + online, deduped, ranked
2. Present candidates as a numbered list with scores
3. **[FORK]** "这些是初步候选，要纳入哪些？全部还是选几篇？"
4. For selected papers, generate survey with structured tables:
   - **方法分类表**: | 类别 | 代表论文 | 核心思路 | 优势 | 局限 |
   - **实验对比表**: | 论文 | 数据集 | 指标1 | 指标2 | 亮点 |
   - **研究空白与趋势**: open problems, emerging directions
   - **结论与建议**: 当前方向的成熟度判断、主流方法对比结论、研究机会在哪里
5. **[FORK]** "要修改、补充、还是导出？（BibTeX / Markdown / 保存综述）"

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
- Don't auto-save files. Export/save only when user chooses in the FORK.
"""

CITATION_EXPLORE_SKILL = """\
---
name: citation-explore
description: Citation chain exploration. Triggers on "引用链", "谁引了", "citation", "参考文献", "这篇引了谁".
---

# Citation Exploration

## Flow

1. Call `paper_citation_trace(paper_id, direction="both", max_depth=2)` — traces 2 levels automatically
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

1. Call `paper_auto_triage(top_n=5)` — automatically classifies recent unread papers into important/to_read/skip using existing relevance scores
2. Present the three buckets as tables:

   **⭐ 重要**: | # | 标题 | 评分 | 入选理由 |
   **📖 待读**: | # | 标题 | 评分 | 简评 |
   **⏭️ 跳过**: | # | 标题 | 评分 | 跳过理由 |
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

After marking, **[FORK]** "已标记完成。要保存筛选报告？还是先这样？"

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

1. Call `paper_quick_scan(topic, limit=20)` for recent work landscape
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
- Don't auto-save files. Export only when user chooses in the FORK.
"""

# Registry for programmatic access
WORKFLOW_SKILLS: dict[str, str] = {
    "daily-reading": DAILY_READING_SKILL,
    "deep-dive": DEEP_DIVE_SKILL,
    "literature-survey": LITERATURE_SURVEY_SKILL,
    "citation-explore": CITATION_EXPLORE_SKILL,
    "paper-triage": PAPER_TRIAGE_SKILL,
    "research-insight": RESEARCH_INSIGHT_SKILL,
}
