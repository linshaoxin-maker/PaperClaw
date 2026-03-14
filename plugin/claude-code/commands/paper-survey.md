---
description: Quick literature survey — one-call topic scan, then optional full survey
argument-hint: <topic>
allowed-tools: [
  "mcp__paper-agent__paper_quick_scan",
  "mcp__paper-agent__paper_batch_show",
  "mcp__paper-agent__paper_compare",
  "mcp__paper-agent__paper_export",
  "mcp__paper-agent__paper_group_add",
  "Read",
  "Write"
]
---

# Paper Survey

> Workflow detail: read `.claude/skills/literature-survey/SKILL.md` for full survey template, quick/full mode rules, and output format.

Quick-first literature survey.

## Process

1. Parse $ARGUMENTS as the survey topic
2. Call `paper_quick_scan(topic=$ARGUMENTS, limit=20)` — local + online, deduped, ranked
3. Present candidates as numbered list with scores
4. **ASK**: "这些是初步候选，要纳入哪些？全部还是选几篇？"
5. For selected papers, generate survey narrative in Chinese
6. **ASK**: "要修改、补充、还是导出？（BibTeX / Markdown / 保存综述）"
7. If user wants to export/save:
   - `paper_export(paper_ids, format="bibtex")` for BibTeX
   - `paper_group_add(name="survey-{topic}", paper_ids, create_if_missing=True)` to group
   - Write survey to `survey/{topic}.md` if saving narrative

Default is quick mode (20 candidates). Full mode (40+) only when user explicitly asks.
