---
description: Research trend analysis — publication trends, sub-direction heat map
argument-hint: <topic>
allowed-tools: [
  "mcp__paper-agent__paper_quick_scan",
  "mcp__paper-agent__paper_trend_data",
  "mcp__paper-agent__paper_save_report",
  "Read"
]
---

# Research Insight

> Workflow detail: read `.claude/skills/research-insight/SKILL.md` for quick/full mode rules, trend table format, and export options.

Quick trend analysis for a research topic.

## Process

1. Parse $ARGUMENTS as the topic
2. **Context carry-over**:
   - If user explicitly references existing papers ("根据刚才的", "用这些做趋势分析"): use those papers directly as landscape
   - If papers in context on the same topic but reference is ambiguous: ASK "刚才找到了 N 篇相关论文，基于这些做趋势分析？还是重新搜索？"
   - If no context → call `paper_quick_scan(topic=$ARGUMENTS, limit=20)` directly
3. Call `paper_trend_data(topic=$ARGUMENTS, years_back=3)` for trend numbers
4. Present as structured tables:

   **趋势总览**
   | 子方向 | 2023 | 2024 | 2025 | 趋势 |
   |--------|------|------|------|------|

   **热门论文**
   | # | 标题 | 年份 | 引用 | 一句话 |
   |---|------|------|------|--------|

   **结论与建议**: 这个方向整体趋势判断，哪些子方向在上升/下降，当前入场的时机建议
5. **Auto-save**: call `paper_save_report(report_type="insight", content=<insight markdown>, filename="{topic}-{YYYY-MM-DD}.md")` to persist the insight report
6. Tell user: "📄 趋势洞察已保存至 {path}。要深入某个子方向？还是先这样？"
