---
description: Compare multiple papers side by side — methods, results, architecture
allowed-tools: [
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_batch_show",
  "mcp__paper-agent__paper_compare",
  "mcp__paper-agent__paper_export",
  "Write"
]
---

# Paper Compare

Compare multiple papers on selected dimensions.

## Process

1. If $ARGUMENTS contains paper IDs, use them directly
2. Otherwise, ask the user which papers to compare
   - Optionally search first: `paper_search(query)` to find candidates
3. Ask which dimensions to compare:
   - a) 方法架构  b) 实验结果  c) 适用场景  d) 全部
4. Call `paper_compare(paper_ids, aspects)` to get structured comparison data
5. Generate comparison tables in Chinese:

   **方法对比**:
   | 维度 | 论文A | 论文B | 论文C |
   |------|-------|-------|-------|
   | 方法 | ... | ... | ... |
   | 关键技术 | ... | ... | ... |
   | 主要结果 | ... | ... | ... |
   | 适用场景 | ... | ... | ... |

   **结论与建议**: 明确判断哪种方法在什么场景下最优，给出选型建议
7. Ask: "要保存对比表格吗？或者基于这些写 survey？"
8. If save requested, write to file
9. If export requested, call `paper_export(paper_ids, format="bibtex")`
