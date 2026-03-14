---
name: deep-dive
description: Deep analysis of a single paper. Triggers on "分析这篇", "deep dive", "这篇论文讲了什么", paper ID or arXiv ID input.
---

# Deep Dive Analysis

## Flow

1. **Resolve paper_id from context**: If the user refers to a paper by index (e.g. "第3篇", "分析上面那篇"), resolve it from the papers discussed earlier in this conversation. If user gives an explicit paper ID or arXiv ID, use that directly.
2. Call `paper_show(paper_id)` to get full paper details
3. Call `paper_profile()` to understand user's research context
4. **[FORK]** "全面分析，还是关注某个角度？（方法/实验/跟你的关联）"
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

If `first_use` is true in the response, tell the user: "（首次自动记录）我把分析笔记保存到了工作区（.paper-agent/），方便以后查阅。如果不需要自动记录，告诉我'不要记录'就行。"
If `first_use` is false, just briefly say: "已记录到工作区。"

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
