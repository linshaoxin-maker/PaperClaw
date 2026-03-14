---
description: One-call morning pipeline — context recovery, collect, digest, auto-mark
allowed-tools: [
  "mcp__paper-agent__paper_morning_brief",
  "mcp__paper-agent__paper_show"
]
---

# Start My Day

Generate today's personalized paper digest in one call.

## Process

1. Call `paper_morning_brief(days=1)` — this single tool does context + collect + digest + auto-mark
2. Present results in Chinese:
   - **今日概览**: new papers collected, scoring summary
   - **高置信推荐**: top papers with title, score, one-line reason
   - If mode is "workspace": mention auto-marked papers
3. **ASK**: "深入看哪篇？保存今日摘要？还是先这样？"
4. If user picks a paper, call `paper_show(paper_id)` for details
5. If user wants to save, write digest to `daily/{YYYY-MM-DD}.md`
