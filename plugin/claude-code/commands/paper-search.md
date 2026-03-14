---
description: Search the local paper library by keyword, topic, or method name
argument-hint: <query>
allowed-tools: [
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_show"
]
---

# Paper Search

Search the local paper library.

## Process

1. Parse $ARGUMENTS as the search query
2. Call `paper_search(query=$ARGUMENTS)` to search the library
3. Present results as a concise list — each paper with title, score, and one-line summary
4. If the user asks about a specific paper from the results, call `paper_show(paper_id)` for details

## Output Format

找到 N 篇相关论文：

| # | 标题 | 评分 | 关键词 | 一句话总结 |
|---|------|------|--------|-----------|
| 1 | ... | 8.5 | GNN, placement | ... |

**结论**: [搜索结果中的关键发现，如"这些论文主要分为X和Y两个方向"]

需要查看某篇的详细信息吗？
