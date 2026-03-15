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
- When routing to a tool directly (morning_brief, auto_triage, citation_trace), call it and present results. No extra questions.
- When routing to a skill, follow that skill's fork-only checkpoints.
- Never list more than 3 options. Prefer smart default + "或者？"
- Workspace operations (note_add, reading_status, group_add) are automatic. Report saving via `paper_save_report` is automatic in each workflow. Additional export (BibTeX) is opt-in via each workflow's FORK.
