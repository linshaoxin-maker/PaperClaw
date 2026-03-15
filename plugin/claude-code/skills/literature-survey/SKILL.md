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
7. **[FORK]** "文献综述已保存至 {path}。要修改、补充、还是导出 BibTeX？"

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
