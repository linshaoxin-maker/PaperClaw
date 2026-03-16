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
     "研究 Ideas 已保存至 {path}。\n💡 **下一步建议**：\n1. 为 [{top_idea_name}] 做实验计划 — 可行性最高\n2. 组一个 reading pack 补充背景知识\n（说编号或告诉我你想做什么）"

   - If top idea is novel but needs more background:
     "研究 Ideas 已保存至 {path}。\n💡 **下一步建议**：\n1. 组一个 reading pack — [{top_idea_name}] 需要补充 [{missing_area}] 的知识\n2. 搜索 [{missing_area}] 的相关论文\n（说编号或告诉我你想做什么）"

### Experiment Planning Mode

1. Resolve single paper ID
2. Call `paper_experiment_plan(paper_id)` — analyzes reproducible/improvable/replaceable parts
3. Present plan with workload and risk assessment
4. **Auto-save**: call `paper_save_report(report_type="experiment_plan", content=<plan markdown>, filename="{paper_id}-plan.md")`

5. **[CONTEXT-AWARE FORK]** — Based on the experiment plan:

   - If paper has code available:
     "实验计划已保存至 {path}。\n💡 **下一步建议**：\n1. 下载这篇的 PDF 和代码 — 开始复现\n2. 找 [{baseline_name}] 的论文做对比实验\n（说编号或告诉我你想做什么）"

   - If paper has no code:
     "实验计划已保存至 {path}。\n💡 **下一步建议**：\n1. 搜索有代码的同方向论文 — 可以作为实现参考\n2. 组一个 reading pack 理解实现细节\n（说编号或告诉我你想做什么）"

### Reading Pack Mode

1. Get research question from user (or infer from context)
2. Call `paper_reading_pack(question, limit=10)`
3. Present ordered reading list with rationale and depth suggestion
4. **Auto-save**: call `paper_save_report(report_type="reading_pack", content=<reading pack markdown>, filename="{question_slug}.md")`

5. **[CONTEXT-AWARE FORK]** — Based on the reading pack:

   "阅读包已保存至 {path}（{N} 篇，建议阅读顺序已标注）。\n💡 **下一步建议**：\n1. 从第一篇开始 — 深入分析 [{first_paper_title}]\n2. 批量下载这 {N} 篇的 PDF\n（说编号或告诉我你想做什么）"

## Rules

- Always try to set research context first for better personalization.
- 2 checkpoints max per mode.
- Always auto-save outputs via `paper_save_report`. Additional export (BibTeX) is opt-in via FORK.
- FORK suggestions must reference actual idea names, paper titles, and feasibility assessments from the result.
