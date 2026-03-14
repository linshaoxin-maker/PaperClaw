---
name: research-insight
description: Research trend analysis and insight generation. Triggers on "趋势", "trend", "这个方向火不火", "research insight", "方向分析".
---

# Research Insight

## Flow

1. Call `paper_quick_scan(topic, limit=20)` for recent work landscape
2. Call `paper_trend_data(topic, years_back=3)` for publication counts and trends
3. Present as structured tables:

   **趋势总览**: | 子方向 | 2023 | 2024 | 2025 | 趋势 |
   **热门论文**: | # | 标题 | 年份 | 引用 | 一句话 |
   **主要会议分布**: | 会议 | 论文数 | 代表工作 |
   **结论与建议**: 方向整体判断（上升/成熟/衰退）、最有潜力的子方向、入场时机建议
4. **[FORK]** "要深入某个子方向？导出分析报告？还是先这样？"

## If user wants to go deeper

Route to **literature-survey** skill with the selected sub-direction as topic.

## If user wants to export

Write insight report to `insight/{topic}-{YYYY-MM-DD}.md`.

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
- Don't auto-save files. Export only when user chooses in the FORK.
