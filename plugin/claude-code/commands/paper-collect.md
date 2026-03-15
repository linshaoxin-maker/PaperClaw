---
description: Collect papers from arXiv and run LLM relevance scoring
argument-hint: [days_back]
allowed-tools: [
  "mcp__paper-agent__paper_collect",
  "mcp__paper-agent__paper_stats",
  "mcp__paper-agent__paper_watch_check",
  "mcp__paper-agent__paper_save_report"
]
---

# Paper Collect

Collect papers from configured arXiv categories.

## Process

1. Parse $ARGUMENTS for optional `days_back` parameter (default: 7)
2. Call `paper_collect(days=$days_back)` to fetch and score papers
3. Call `paper_stats()` to show updated library overview
4. Present results in Chinese:
   - **收集完成**: N papers collected (X new, Y duplicate)
   - **库概览**: total papers, high/low confidence counts
   - **热门主题**: top topics from the library
5. If user wants to save ("保存收集结果"), call `paper_save_report(report_type="daily_digest", content=<summary markdown>)`
