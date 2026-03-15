---
name: deep-dive
description: Deep analysis of a single paper. Triggers on "分析这篇", "deep dive", "这篇论文讲了什么", paper ID or arXiv ID input.
---

# Deep Dive Analysis

## Flow

1. **Resolve paper_id from context**: If the user refers to a paper by index (e.g. "第3篇", "分析上面那篇"), resolve it from the papers discussed earlier in this conversation. If user gives an explicit paper ID or arXiv ID, use that directly.
2. Call `paper_show(paper_id)` to get full paper details
3. Call `paper_profile()` to understand user's research context
4. **Check for full text**: Try `paper_sections(paper_id)` — if parsed, the analysis will use full text. If not parsed but a PDF exists, call `paper_parse(paper_id)` to parse it first.
5. **Extract structured profile**: Call `paper_extract(paper_id)` to get task/method/dataset/baseline/metric data.
6. **[FORK]** "全面分析，还是关注某个角度？（方法/实验/跟你的关联/可信度）"
7. Generate analysis based on user's choice (or full analysis by default). If full text is available, use `paper_ask(paper_id, question)` for specific questions.

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

**[FORK]** Present options based on mode:
- workspace: "已自动记录到工作区，分析笔记已保存至 {path}。要看引用链？还是先这样？"
- lightweight: "分析笔记已保存至 {path}。要看引用链？还是先这样？"

## If user wants citation trace

Route to `paper_citation_trace(paper_id)`.

## Rules

- 2 checkpoints (analysis angle + after analysis). Both workspace note-add and file save are automatic.
- If user explicitly says "不要记录", skip the note_add call and the save_report call.
