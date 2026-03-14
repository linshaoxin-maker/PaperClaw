---
description: Research trend analysis — publication trends, sub-direction heat map
argument-hint: <topic>
allowed-tools: [
  "mcp__paper-agent__paper_quick_scan",
  "mcp__paper-agent__paper_trend_data",
  "Read"
]
---

# Research Insight

> Workflow detail: read `.claude/skills/research-insight/SKILL.md` for quick/full mode rules, trend table format, and export options.

Quick trend analysis for a research topic.

## Process

1. Parse $ARGUMENTS as the topic
2. Call `paper_quick_scan(topic=$ARGUMENTS, limit=20)` for recent work
3. Call `paper_trend_data(topic=$ARGUMENTS, years_back=3)` for trend numbers
4. Present as structured tables:

   **趋势总览**
   | 子方向 | 2023 | 2024 | 2025 | 趋势 |
   |--------|------|------|------|------|

   **热门论文**
   | # | 标题 | 年份 | 引用 | 一句话 |
   |---|------|------|------|--------|

   **结论与建议**: 这个方向整体趋势判断，哪些子方向在上升/下降，当前入场的时机建议
5. **ASK**: "要深入某个子方向？导出分析报告？还是先这样？"
