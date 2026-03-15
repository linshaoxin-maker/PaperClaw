---
description: Research planning — generate ideas, experiment plans, or reading packs from papers
argument-hint: <topic or paper_id>
allowed-tools: [
  "mcp__paper-agent__paper_show",
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_quick_scan",
  "mcp__paper-agent__paper_ideate",
  "mcp__paper-agent__paper_experiment_plan",
  "mcp__paper-agent__paper_reading_pack",
  "mcp__paper-agent__paper_research",
  "mcp__paper-agent__paper_extract",
  "mcp__paper-agent__paper_profile",
  "mcp__paper-agent__paper_save_report",
  "Read",
  "Write"
]
---

# Paper Plan

> Workflow detail: read `.claude/skills/research-planning/SKILL.md` for full planning modes and output format.

Bridge from literature understanding to research action.

## Modes

### Ideation (default)
When user says "给我灵感" / "research ideas" / "这篇能给我什么启发":
1. Call `paper_ideate(paper_ids, user_context)` to generate research ideas
2. Present as structured list with feasibility and novelty ratings

### Experiment Planning
When user says "实验计划" / "怎么复现改进" / "experiment plan":
1. Call `paper_experiment_plan(paper_id)` to generate experiment plan
2. Present with timeline, resource requirements, and risk assessment

### Reading Pack
When user says "给我组个 reading pack" / "怎么读这个方向":
1. Call `paper_reading_pack(topic)` to generate a structured reading list
2. Present with reading order, difficulty progression, and time estimates

## Process

1. Parse $ARGUMENTS to determine mode and target (paper_id or topic)
2. Call `paper_profile()` to understand user's research context
3. Execute the appropriate mode
4. **Auto-save**: call `paper_save_report(report_type="research_plan", content=<plan markdown>, filename="{topic}-plan.md")`
5. Tell user: "📄 研究计划已保存至 {path}。要调整方向？还是先这样？"
