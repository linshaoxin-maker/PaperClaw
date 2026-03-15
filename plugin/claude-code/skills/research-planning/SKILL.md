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
5. **[FORK]** "研究 Ideas 已保存至 {path}。深入某个想法？组 reading pack？还是先这样？"

### Experiment Planning Mode

1. Resolve single paper ID
2. Call `paper_experiment_plan(paper_id)` — analyzes reproducible/improvable/replaceable parts
3. Present plan with workload and risk assessment
4. **Auto-save**: call `paper_save_report(report_type="experiment_plan", content=<plan markdown>, filename="{paper_id}-plan.md")`
5. **[FORK]** "实验计划已保存至 {path}。开始某个实验？需要补充阅读？还是先这样？"

### Reading Pack Mode

1. Get research question from user (or infer from context)
2. Call `paper_reading_pack(question, limit=10)`
3. Present ordered reading list with rationale and depth suggestion
4. **Auto-save**: call `paper_save_report(report_type="reading_pack", content=<reading pack markdown>, filename="{question_slug}.md")`
5. **[FORK]** "阅读包已保存至 {path}。调整顺序？加减论文？还是先这样？"

## Rules

- Always try to set research context first for better personalization.
- 2 checkpoints max per mode.
- Always auto-save outputs via `paper_save_report`. Additional export (BibTeX) is opt-in via FORK.
