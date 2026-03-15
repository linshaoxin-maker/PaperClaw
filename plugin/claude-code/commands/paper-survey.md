---
description: Quick literature survey — one-call topic scan, then optional full survey
argument-hint: <topic>
allowed-tools: [
  "mcp__paper-agent__paper_quick_scan",
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_batch_show",
  "mcp__paper-agent__paper_compare",
  "mcp__paper-agent__paper_compare_table",
  "mcp__paper-agent__paper_extract",
  "mcp__paper-agent__paper_export",
  "mcp__paper-agent__paper_group_add",
  "mcp__paper-agent__paper_trend_data",
  "mcp__paper-agent__paper_field_stats",
  "mcp__paper-agent__paper_credibility",
  "mcp__paper-agent__paper_credibility_batch",
  "mcp__paper-agent__paper_survey_collect",
  "mcp__paper-agent__paper_save_report",
  "Read",
  "Write"
]
---

# Paper Survey

> Workflow detail: read `.claude/skills/literature-survey/SKILL.md` for full survey template, quick/full mode rules, and output format.

Quick-first literature survey.

## Process

### Step 1 — Resolve papers

- **Explicit reference** ("根据已有的", "用刚才的", "基于这些写综述"): use those papers directly. Go to Step 2 immediately — no candidate listing, no selection question.
- **Ambiguous** (same topic in context): ASK "刚才找到了 N 篇相关论文，直接用这些？还是再补充搜索？"
- **New search**: Call `paper_quick_scan(topic=$ARGUMENTS, limit=20)`, then show candidates as table and ASK "全部纳入还是选几篇？"

### Step 2 — Generate survey

Generate survey narrative in Chinese with structured tables:
- **方法分类表**: | 类别 | 代表论文 | 核心思路 | 优势 | 局限 |
- **实验对比表**: | 论文 | 数据集 | 指标1 | 指标2 | 亮点 |
- **研究空白与趋势**: open problems, emerging directions
- **结论与建议**: 当前方向的成熟度判断、主流方法对比结论、研究机会在哪里

### Step 3 — Auto-save

Call `paper_save_report(report_type="survey", content=<survey markdown>, filename="{topic}.md")` to persist the survey.

Tell user: "📄 文献综述已保存至 {path}。要修改、补充、还是导出 BibTeX？"

Default is quick mode (20 candidates). Full mode (40+) only when user explicitly asks.
