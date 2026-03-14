---
description: Collect latest arXiv papers and generate today's personalized digest
allowed-tools: [
  "mcp__plugin_paper-agent_paper-agent__paper_collect",
  "mcp__plugin_paper-agent_paper-agent__paper_digest",
  "mcp__plugin_paper-agent_paper-agent__paper_stats"
]
---

# Start My Day

Generate today's personalized paper digest.

## Process

1. Call `paper_collect(days=1)` to fetch the latest papers from arXiv
2. Call `paper_digest()` to generate today's recommendations
3. Present results in Chinese with this structure:

```
## 今日概览

今日推荐的 N 篇论文主要聚焦于 **{方向1}** 和 **{方向2}**。

## 高置信推荐（N 篇）

### 1. [[论文标题]]
- **作者**：[作者列表]
- **评分**：X.X/10
- **链接**：[arXiv](链接)
- **一句话总结**：[核心贡献]

## 阅读建议

建议先阅读第 X 篇了解 [方向]，再关注第 Y 篇的 [方法]。
```

## Error Handling

- If library is empty, guide user to run `paper-agent init` and `paper-agent profile create` first
- If collect returns 0 new papers, still generate digest from existing library
