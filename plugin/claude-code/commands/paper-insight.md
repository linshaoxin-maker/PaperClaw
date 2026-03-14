---
description: Research trend analysis — publication trends, sub-direction heat map
argument-hint: <topic>
allowed-tools: [
  "mcp__paper-agent__paper_quick_scan",
  "mcp__paper-agent__paper_trend_data"
]
---

# Research Insight

Quick trend analysis for a research topic.

## Process

1. Parse $ARGUMENTS as the topic
2. Call `paper_quick_scan(topic=$ARGUMENTS, limit=20)` for recent work
3. Call `paper_trend_data(topic=$ARGUMENTS, years_back=3)` for trend numbers
4. Present: overall trend, sub-directions, top venues, notable papers
5. **ASK**: "要深入某个子方向？导出分析报告？还是先这样？"
