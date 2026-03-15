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
| "引用链" / "谁引了这篇" / "citation" | citation-explore skill |
| "筛一下" / "triage" / "哪些值得看" | paper-triage skill |
| "趋势" / "trend" / "这个方向火不火" | research-insight skill |
| Research question (e.g. "RL做placement还有没有新意？") | `paper_research` tool directly |
| "这篇可信吗" / "能不能复现" / "credibility" | `paper_credibility` tool directly |
| "跟踪这个方向" / "watch" / "关注这个作者" | `paper_watch` tool directly |
| "我觉得这篇不行" / "这类少推" / feedback | `paper_feedback` tool directly |
| "这篇能给我什么启发" / "research ideas" | research-planning skill (ideation mode) |
| "实验计划" / "能怎么复现改进" / "experiment plan" | research-planning skill (experiment mode) |
| "给我组个 reading pack" / "怎么读" | research-planning skill (reading pack mode) |
| "保存搜索结果" / "存一下这个列表" | `paper_save_report` tool directly |
| "推荐和我课题相关的" / "recommend" | `paper_recommend` tool directly |
| "抽取结构化信息" / "extract" / "比较表格" | `paper_extract` or `paper_compare_table` |
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
- When routing to a tool directly (morning_brief, auto_triage, citation_trace), call it and present results. **Then follow the Next-Step Prediction rules below.**
- When routing to a skill, follow that skill's fork-only checkpoints.
- Never list more than 3 options. Prefer smart default + "或者？"
- Workspace operations (note_add, reading_status, group_add) are automatic. Report saving via `paper_save_report` is automatic in each workflow. Additional export (BibTeX) is opt-in via each workflow's FORK.

## ⚡ Next-Step Prediction Engine (MANDATORY for all tool/skill completions)

**Every time a tool call or skill completes, you MUST proactively suggest 2-3 context-aware next actions.** This is the core UX differentiator — the system anticipates what the researcher needs next.

### Prediction Rules

After ANY tool/skill completion, analyze the result data and generate personalized suggestions:

| Just completed | Result signals | Suggest |
|---|---|---|
| `paper_search` / `paper_quick_scan` | Found N papers | "找到 {N} 篇。要筛选一下（triage）？还是直接看评分最高的 [{top_title}]？" |
| `paper_search` | 0 results | "本地没找到。要在线搜索？还是换个关键词？" |
| `paper_morning_brief` | Has important papers | "今天有 {N} 篇高相关。先看 [{top_title}]（{score}分）？还是先筛选一轮？" |
| `paper_morning_brief` | Empty digest | "今天没有新论文。要扫描一下 [{user_topic}] 的最新进展？" |
| `paper_show` | Paper loaded | "要深入分析这篇？看引用链？还是找类似的论文？" |
| `paper_auto_triage` | Has important bucket | "筛出 {N} 篇重要论文。要批量下载 PDF？还是先深入看 [{top_important_title}]？" |
| `paper_auto_triage` | All skip | "这批论文跟你方向关联不大。要调整 profile？还是换个方向搜索？" |
| `paper_citation_trace` | Found key nodes | "发现 {N} 个关键节点。要把这些加到阅读分组？还是继续追踪 [{key_node_title}]？" |
| `paper_credibility` | Low confidence | "这篇可信度偏低（{reason}）。要找同方向更可靠的替代论文？" |
| `paper_credibility` | High confidence | "可信度高。要深入分析方法细节？还是看实验能不能复现？" |
| `paper_extract` | Profile extracted | "结构化信息已提取。要跟其他论文对比？还是基于这篇做实验计划？" |
| `paper_compare` / `paper_compare_table` | Comparison done | "对比完成。要生成综述？还是导出 BibTeX 写 related work？" |
| `paper_feedback` | Feedback recorded | "已记录。后续推荐会参考你的偏好。要继续看下一篇？" |
| `paper_recommend` | Has recommendations | "推荐了 {N} 篇。要筛选一下？还是直接看 [{top_title}]？" |
| `paper_watch` | Watch added | "已关注。要看这个方向的趋势分析？" |
| `paper_find_and_download` | PDF downloaded | "PDF 已下载。要解析全文做深度分析？" |
| `paper_research` | Answer generated | "要把涉及的论文做个对比？还是深入某篇？" |

### Suggestion Format

Always use this format at the end of every response:

```
---
💡 **下一步建议**：
1. [最可能的下一步 — 基于当前结果数据]
2. [第二可能的下一步]
（直接说编号或描述你想做的事）
```

### Key Principles

1. **Data-driven**: Suggestions must reference actual data from the result (paper titles, scores, counts). Never give generic suggestions.
2. **Max 3 options**: Never overwhelm. 2 is ideal, 3 is max.
3. **Default action first**: The most likely next action should be option 1.
4. **Carry context**: When user picks an option, carry all relevant paper IDs, scores, and context forward. Never ask the user to re-specify.
5. **Exit is implicit**: Don't add "还是先这样？" as an option — if the user wants to stop, they'll just stop or say something new.
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

4. **Auto-save**: call `paper_save_report(report_type="daily_digest", content=<digest markdown>, filename="{YYYY-MM-DD}.md")` using the daily-digest-template. Tell user the saved path.

5. **[CONTEXT-AWARE FORK]** — Based on the digest result, suggest next steps:

   - If digest has ≥1 high-confidence paper:
     "今日摘要已保存至 {path}。\\n💡 **下一步建议**：\\n1. 深入分析 [{top_paper_title}]（{score}分，{reason}）\\n2. 先筛选一轮，确认哪些值得读\\n（说编号或告诉我你想做什么）"

   - If digest is empty:
     "今天没有新的高相关论文。\\n💡 **下一步建议**：\\n1. 扫描一下 [{user_primary_topic}] 的最新进展\\n2. 看看 watchlist 有没有更新\\n（说编号或告诉我你想做什么）"

   - If watchlist has updates:
     Append: "另外，[{watch_item}] 有 {N} 篇新论文，要看看吗？"

## If user picks a paper

Hand off to the **deep-dive** skill with the selected paper ID. Carry the paper's score, topics, and recommendation_reason as context.

## Workspace behavior

The `paper_morning_brief` response includes a `mode` field:
- `"workspace"`: top picks were auto-marked as `to_read`.
  - If `auto_marked` > 0 AND this is the user's first time seeing auto-marking (no prior reading stats), explain: "（首次自动标记）我把 N 篇高相关论文自动标记为'待读'，方便你追踪阅读进度。这个行为可以通过切换到 lightweight 模式关闭。"
  - On subsequent uses, just briefly mention: "已自动标记 N 篇为待读。"
- `"lightweight"`: just present the digest, no status talk.

## Rules

- Only 1 checkpoint (the fork above). Everything else is automatic.
- Don't ask about collection parameters, source selection, or date ranges unless user specifies.
- FORK suggestions must reference actual paper titles and scores from the digest result. Never give generic options.
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

If `first_use` is true in the response, tell the user: "（首次自动记录）我把分析笔记保存到了工作区（.paper-agent/），方便以后查阅。如果不需要自动记录，告诉我'不要记录'就行。"
If `first_use` is false, just briefly say: "已记录到工作区。"

**Auto-save**: call `paper_save_report(report_type="analysis", content=<analysis markdown>, filename="{paper_id}.md")` to persist the analysis as a file.

**[CONTEXT-AWARE FORK]** — Based on the analysis result, suggest next steps:

Analyze the paper's characteristics and suggest accordingly:

- If paper has high citation count (>50) or is a seminal work:
  "分析笔记已保存至 {path}。\\n💡 **下一步建议**：\\n1. 追踪引用链 — 看看谁在跟进这个方向\\n2. 找类似方法的论文做对比\\n（说编号或告诉我你想做什么）"

- If paper has code available:
  "分析笔记已保存至 {path}。\\n💡 **下一步建议**：\\n1. 做实验计划 — 这篇有代码，可以复现/改进\\n2. 追踪引用链看后续工作\\n（说编号或告诉我你想做什么）"

- If paper's method is novel (novelty_claim is strong):
  "分析笔记已保存至 {path}。\\n💡 **下一步建议**：\\n1. 看看这个方法能不能用到你的课题 — 生成 research ideas\\n2. 找同方向的论文做对比\\n（说编号或告诉我你想做什么）"

- Default:
  "分析笔记已保存至 {path}。\\n💡 **下一步建议**：\\n1. 追踪引用链\\n2. 找 [{paper_method_family}] 方向的更多论文\\n（说编号或告诉我你想做什么）"

## If user picks citation trace

Route to `paper_citation_trace(paper_id)`. Carry the paper's method_family and topics as context for the citation exploration.

## Rules

- 2 checkpoints (analysis angle + after analysis). Both workspace note-add and file save are automatic.
- If user explicitly says "不要记录", skip the note_add call and the save_report call.
- FORK suggestions must be based on the actual analysis result (citation count, code availability, method novelty). Never give the same generic options.
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
6. **Auto-save**: call `paper_save_report(report_type="survey", content=<survey markdown>, filename="{topic}.md")` to persist the survey.

7. **[CONTEXT-AWARE FORK]** — Based on the survey result, suggest next steps:

   - If survey found clear research gaps:
     "文献综述已保存至 {path}（涵盖 {N} 篇论文）。\\n💡 **下一步建议**：\\n1. 基于发现的研究空白生成 research ideas\\n2. 导出 {N} 篇论文的 BibTeX — 可以直接用在 related work\\n（说编号或告诉我你想做什么）"

   - If survey shows a dominant method family:
     "文献综述已保存至 {path}。\\n💡 **下一步建议**：\\n1. 深入分析 [{dominant_method}] 方向的代表论文 [{top_paper_title}]\\n2. 导出 BibTeX 写 related work\\n（说编号或告诉我你想做什么）"

   - If survey covers many diverse methods:
     "文献综述已保存至 {path}。\\n💡 **下一步建议**：\\n1. 看看 [{topic}] 的趋势分析 — 哪个子方向在上升\\n2. 导出 BibTeX\\n（说编号或告诉我你想做什么）"

## If user wants to export

- `paper_export(paper_ids, format)` for BibTeX/markdown
- `paper_group_add(name="survey-{topic}", paper_ids, create_if_missing=True)` to group papers

## Quick mode (default)

`paper_quick_scan` returns 15-20 candidates with one-line summaries. Present this list and let user decide next steps. This IS the survey for most cases.

## Full mode

Only when user explicitly asks for "完整综述" / "full survey" / "详细一点":
- Expand to 40+ candidates via `paper_quick_scan(topic, limit=40)`
- Generate multi-section survey with per-paper analysis

## Rules

- 2 checkpoints max (selection + revision/export). Don't ask about search parameters.
- Default to quick mode. Don't generate a full survey unless asked.
- Always auto-save the survey via `paper_save_report`. Additional export (BibTeX) is opt-in via FORK.
- FORK suggestions must reference actual paper counts, method families, and research gaps from the survey result.
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
3. **Auto-save**: call `paper_save_report(report_type="citation_map", content=<citation tree markdown>, filename="{seed_id}.md")` to persist the citation map.

4. **[CONTEXT-AWARE FORK]** — Based on the citation trace result, suggest next steps:

   - If found high-citation key nodes:
     "引用图谱已保存至 {path}（发现 {N} 个关键节点）。\\n💡 **下一步建议**：\\n1. 深入分析关键节点 [{key_node_title}]（{citations} 次引用）\\n2. 把这 {N} 篇加到阅读分组 — 方便后续追踪\\n（说编号或告诉我你想做什么）"

   - If found recent follow-up papers (last 1-2 years):
     "引用图谱已保存至 {path}。\\n💡 **下一步建议**：\\n1. 看看最新的跟进工作 [{recent_paper_title}]（{year}）\\n2. 基于引用链做这个方向的综述\\n（说编号或告诉我你想做什么）"

   - If citation chain is thin (few citations):
     "引用图谱已保存至 {path}。引用链比较短，这可能是个较新的方向。\\n💡 **下一步建议**：\\n1. 搜索 [{seed_method}] 相关的更多论文\\n2. 看看这个方向的趋势分析\\n（说编号或告诉我你想做什么）"

## If user picks a paper to trace further

Call `paper_citation_trace(new_paper_id)` again for the selected paper.

## If user wants to group

Call `paper_group_add(name="citation-{seed_title}", paper_ids=[...], create_if_missing=True)`.

## If user wants BibTeX export

Call `paper_export(paper_ids, format="bibtex")` for references.

## Rules

- Only 1 checkpoint. The recursive trace is handled by `paper_citation_trace` in one call.
- Don't ask about direction (both by default) or depth unless user specifies.
- Present the tree concisely: title + year + direction for each paper.
- If workspace mode, mention discovered papers were saved to library.
- FORK suggestions must reference actual key node titles, citation counts, and years from the trace result.
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

After marking, **auto-save**: call `paper_save_report(report_type="triage", content=<report markdown>, filename="{topic}-{YYYY-MM-DD}.md")` using triage-template.

**[CONTEXT-AWARE FORK]** — Based on the triage result, suggest next steps:

- If important bucket has papers with PDFs available:
  "已标记完成，筛选报告已保存至 {path}。\\n💡 **下一步建议**：\\n1. 批量下载 {N} 篇重要论文的 PDF\\n2. 深入分析 [{top_important_title}]（{score}分）\\n（说编号或告诉我你想做什么）"

- If important bucket has papers but no PDFs:
  "已标记完成，筛选报告已保存至 {path}。\\n💡 **下一步建议**：\\n1. 深入分析 [{top_important_title}]（{score}分）\\n2. 搜索并下载这些论文的 PDF\\n（说编号或告诉我你想做什么）"

- If important bucket is empty but to_read has papers:
  "没有特别突出的论文，但有 {N} 篇值得一读。\\n💡 **下一步建议**：\\n1. 看看 [{top_to_read_title}] — 评分最高的待读论文\\n2. 换个方向搜索\\n（说编号或告诉我你想做什么）"

- If all papers are skip:
  "这批论文跟你方向关联不大。\\n💡 **下一步建议**：\\n1. 调整 research profile — 可能关键词需要更新\\n2. 换个方向搜索\\n（说编号或告诉我你想做什么）"

## Custom source

If user provides specific paper IDs or says "筛这些":
- Call `paper_auto_triage(paper_ids=[...])` with the specific IDs

## Rules

- Only 1 checkpoint (confirm/adjust). Classification is automatic via `paper_auto_triage`.
- Don't ask about criteria — use profile-based relevance scores by default.
- Don't ask about source — default to recent unread papers.
- Always use tables, never bullet-point lists for paper results.
- Always include a 结论 section explaining why the classification matters.
- FORK suggestions must reference actual paper titles and counts from the triage result.
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
4. **Auto-save**: call `paper_save_report(report_type="insight", content=<insight markdown>, filename="{topic}-{YYYY-MM-DD}.md")` to persist the insight report.

5. **[CONTEXT-AWARE FORK]** — Based on the trend analysis result, suggest next steps:

   - If found a rising sub-direction:
     "趋势洞察已保存至 {path}。\\n💡 **下一步建议**：\\n1. 深入 [{rising_subdirection}] — 这个子方向在快速上升\\n2. 做一个 [{rising_subdirection}] 的文献综述\\n（说编号或告诉我你想做什么）"

   - If found a dominant/mature direction:
     "趋势洞察已保存至 {path}。\\n💡 **下一步建议**：\\n1. 分析 [{top_paper_title}] — 这个方向的代表工作\\n2. 找研究空白 — 看看还有什么没被做过\\n（说编号或告诉我你想做什么）"

   - If the direction is declining:
     "趋势洞察已保存至 {path}。这个方向发文量在下降。\\n💡 **下一步建议**：\\n1. 看看相邻方向 [{related_topic}] 的趋势\\n2. 分析为什么在下降 — 是被新方法替代了吗？\\n（说编号或告诉我你想做什么）"

## If user wants to go deeper

Route to **literature-survey** skill with the selected sub-direction as topic.

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
- Always auto-save insight report via `paper_save_report`. Additional actions are opt-in via FORK.
- FORK suggestions must reference actual sub-directions, paper titles, and trend signals from the analysis result.
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
4. **Auto-save**: call `paper_save_report(report_type="ideation", content=<ideas markdown>, filename="{topic}-ideas-{YYYY-MM-DD}.md")`

5. **[CONTEXT-AWARE FORK]** — Based on the ideation result:

   - If top idea has high feasibility:
     "研究 Ideas 已保存至 {path}。\\n💡 **下一步建议**：\\n1. 为 [{top_idea_name}] 做实验计划 — 可行性最高\\n2. 组一个 reading pack 补充背景知识\\n（说编号或告诉我你想做什么）"

   - If top idea is novel but needs more background:
     "研究 Ideas 已保存至 {path}。\\n💡 **下一步建议**：\\n1. 组一个 reading pack — [{top_idea_name}] 需要补充 [{missing_area}] 的知识\\n2. 搜索 [{missing_area}] 的相关论文\\n（说编号或告诉我你想做什么）"

### Experiment Planning Mode

1. Resolve single paper ID
2. Call `paper_experiment_plan(paper_id)` — analyzes reproducible/improvable/replaceable parts
3. Present plan with workload and risk assessment
4. **Auto-save**: call `paper_save_report(report_type="experiment_plan", content=<plan markdown>, filename="{paper_id}-plan.md")`

5. **[CONTEXT-AWARE FORK]** — Based on the experiment plan:

   - If paper has code available:
     "实验计划已保存至 {path}。\\n💡 **下一步建议**：\\n1. 下载这篇的 PDF 和代码 — 开始复现\\n2. 找 [{baseline_name}] 的论文做对比实验\\n（说编号或告诉我你想做什么）"

   - If paper has no code:
     "实验计划已保存至 {path}。\\n💡 **下一步建议**：\\n1. 搜索有代码的同方向论文 — 可以作为实现参考\\n2. 组一个 reading pack 理解实现细节\\n（说编号或告诉我你想做什么）"

### Reading Pack Mode

1. Get research question from user (or infer from context)
2. Call `paper_reading_pack(question, limit=10)`
3. Present ordered reading list with rationale and depth suggestion
4. **Auto-save**: call `paper_save_report(report_type="reading_pack", content=<reading pack markdown>, filename="{question_slug}.md")`

5. **[CONTEXT-AWARE FORK]** — Based on the reading pack:

   "阅读包已保存至 {path}（{N} 篇，建议阅读顺序已标注）。\\n💡 **下一步建议**：\\n1. 从第一篇开始 — 深入分析 [{first_paper_title}]\\n2. 批量下载这 {N} 篇的 PDF\\n（说编号或告诉我你想做什么）"

## Rules

- Always try to set research context first for better personalization.
- 2 checkpoints max per mode.
- Always auto-save outputs via `paper_save_report`. Additional export (BibTeX) is opt-in via FORK.
- FORK suggestions must reference actual idea names, paper titles, and feasibility assessments from the result.
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
