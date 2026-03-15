---
name: research-insight
description: Research trend analysis and insight generation. Triggers on "趋势", "trend", "这个方向火不火", "research insight", "方向分析".
---

# Research Insight

## Flow

1. **Context carry-over**:
   - If user explicitly references existing papers ("根据刚才的", "用这些做趋势分析"): use those papers directly as landscape
   - If papers in context on the same topic but reference is ambiguous: ASK "刚才找到了 N 篇相关论文，基于这些做趋势分析？还是重新搜索？"
   - If no context → call `paper_quick_scan(topic, limit=20)` directly
2. Call `paper_trend_data(topic, years_back=3)` for publication counts and trends
3. Present as structured tables:

   **趋势总览**: | 子方向 | 2023 | 2024 | 2025 | 趋势 |
   **热门论文**: | # | 标题 | 年份 | 引用 | 一句话 |
   **主要会议分布**: | 会议 | 论文数 | 代表工作 |
   **结论与建议**: 方向整体判断（上升/成熟/衰退）、最有潜力的子方向、入场时机建议
4. **Auto-save**: call `paper_save_report(report_type="insight", content=<insight markdown>, filename="{topic}-{YYYY-MM-DD}.md")` to persist the insight report.

5. **[CONTEXT-AWARE FORK]** — Based on the trend analysis result, suggest next steps:

   - If found a rising sub-direction:
     "趋势洞察已保存至 {path}。\n💡 **下一步建议**：\n1. 深入 [{rising_subdirection}] — 这个子方向在快速上升\n2. 做一个 [{rising_subdirection}] 的文献综述\n（说编号或告诉我你想做什么）"

   - If found a dominant/mature direction:
     "趋势洞察已保存至 {path}。\n💡 **下一步建议**：\n1. 分析 [{top_paper_title}] — 这个方向的代表工作\n2. 找研究空白 — 看看还有什么没被做过\n（说编号或告诉我你想做什么）"

   - If the direction is declining:
     "趋势洞察已保存至 {path}。这个方向发文量在下降。\n💡 **下一步建议**：\n1. 看看相邻方向 [{related_topic}] 的趋势\n2. 分析为什么在下降 — 是被新方法替代了吗？\n（说编号或告诉我你想做什么）"

## If user wants to go deeper

Route to **literature-survey** skill with the selected sub-direction as topic.

## Quick mode (default)

The above flow IS the quick mode. Two tool calls + AI formatting. No extra questions.

## Full mode

Only when user explicitly asks for "详细分析" / "deep analysis":
- Expand `paper_quick_scan(topic, limit=40)`
- Expand `paper_trend_data(topic, years_back=5)`
- Generate a detailed report with method evolution timeline, key contributor analysis

## Rules

- Only 1 checkpoint. The data gathering is fully automatic via `paper_quick_scan` + `paper_trend_data`.
- Don't ask about time range or sub-topics upfront — use defaults.
- Present trend data as a compact table with arrows (trend: up/down/stable).
- Always auto-save insight report via `paper_save_report`. Additional actions are opt-in via FORK.
- FORK suggestions must reference actual sub-directions, paper titles, and trend signals from the analysis result.
