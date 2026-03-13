---
description: Collect papers from arXiv and run LLM relevance scoring
argument-hint: [days_back]
allowed-tools: [
  "mcp__plugin_paper-agent_paper-agent__paper_collect",
  "mcp__plugin_paper-agent_paper-agent__paper_stats"
]
---

# Paper Collect

Collect papers from configured arXiv categories.

## Process

1. Parse $ARGUMENTS for optional `days_back` parameter (default: 7)
2. Call `paper_collect(days=$days_back)` to fetch and score papers
3. Call `paper_stats()` to show updated library overview
4. Present results:

```
## 收集完成

- 收集论文：N 篇
- 新增论文：N 篇
- 重复跳过：N 篇
- LLM 评分：N 篇

## 库概览
- 总计：N 篇
- 高置信：N 篇
- 待评分：N 篇
- 热门方向：[方向1], [方向2]
```

## Error Handling

- If paper-agent is not initialized, guide user through `paper-agent init`
- If no sources configured, suggest `paper-agent profile create`
