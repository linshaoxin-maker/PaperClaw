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
| "对比" / "compare" / "哪个更好" / "这几篇有什么区别" | paper-compare skill |
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
