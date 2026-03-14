---
description: One-call morning pipeline — context recovery, collect, digest, auto-mark
allowed-tools: [
  "mcp__paper-agent__paper_morning_brief",
  "mcp__paper-agent__paper_show",
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
3. **ASK**: "深入看哪篇？保存今日摘要？还是先这样？"
4. If user picks a paper, call `paper_show(paper_id)` for details
5. If user wants to save, write digest to `daily/{YYYY-MM-DD}.md`
