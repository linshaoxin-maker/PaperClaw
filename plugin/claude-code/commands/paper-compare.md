---
description: Compare multiple papers side by side — methods, results, architecture
allowed-tools: [
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_show",
  "mcp__paper-agent__paper_batch_show",
  "mcp__paper-agent__paper_compare",
  "mcp__paper-agent__paper_compare_table",
  "mcp__paper-agent__paper_extract",
  "mcp__paper-agent__paper_export",
  "mcp__paper-agent__paper_save_report",
  "mcp__paper-agent__paper_credibility",
  "Write"
]
---

# Paper Compare

Compare multiple papers on selected dimensions.

## Process

### Step 1 — Resolve papers

- If $ARGUMENTS contains paper IDs → use them directly
- **Explicit reference** ("对比刚才的", "这几篇对比一下") → use those papers directly
- **Ambiguous** (papers in context, no explicit reference) → ASK "刚才找到的这几篇要对比吗？还是指定其他的？"
- **No context, no IDs** → ask which papers to compare

### Step 2 — Compare

When papers are clear (from explicit reference or IDs), default to **全部维度** comparison. Don't ask "which dimensions" unless user specifies.

Call `paper_compare(paper_ids, aspects)` and generate tables in Chinese:

| 维度 | 论文A | 论文B | 论文C |
|------|-------|-------|-------|
| 方法 | ... | ... | ... |
| 关键技术 | ... | ... | ... |
| 主要结果 | ... | ... | ... |
| 适用场景 | ... | ... | ... |

**结论与建议**: 明确判断哪种方法在什么场景下最优，给出选型建议

### Step 3 — Auto-save

Call `paper_save_report(report_type="comparison", content=<comparison markdown>, filename="{short_title}-{YYYY-MM-DD}.md")` to persist the comparison report.

Tell user: "📄 对比报告已保存至 {path}。要基于这些写 survey？还是先这样？"
