---
description: One-call morning pipeline — context recovery, collect, digest, auto-mark
allowed-tools: [
  "mcp__paper-agent__paper_morning_brief",
  "mcp__paper-agent__paper_show",
  "mcp__paper-agent__paper_watch_check",
  "mcp__paper-agent__paper_watch_digest",
  "mcp__paper-agent__paper_save_report",
  "mcp__paper-agent__paper_reading_status",
  "Read"
]
---

# Start My Day

> Workflow detail: read `.claude/skills/daily-reading/SKILL.md` for full rules, edge cases, and output templates.

Generate today's personalized paper digest in one call.

## Process

1. Call `paper_morning_brief(days=1)` — this single tool does context + collect + digest + auto-mark
2. Present in Chinese with structured format:

   **今日概览**: X 篇新论文，Y 篇高相关

   | # | 标题 | 评分 | 关键词 | 一句话总结 |
   |---|------|------|--------|-----------|

   **结论与建议**: 今日论文主要聚焦于 [方向]，建议优先关注第 X 篇（[理由]）

   If mode is "workspace": mention auto-marked papers
3. **Auto-save**: call `paper_save_report(report_type="daily_digest", content=<digest markdown>, filename="{YYYY-MM-DD}.md")` to persist the digest
4. Tell user: "📄 今日摘要已保存至 {path}"
5. **ASK**: "深入看哪篇？还是先这样？"
6. If user picks a paper, call `paper_show(paper_id)` for details
