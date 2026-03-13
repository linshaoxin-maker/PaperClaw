---
description: Search the local paper library by keyword, topic, or method name
argument-hint: <query>
allowed-tools: [
  "mcp__plugin_paper-agent_paper-agent__paper_search",
  "mcp__plugin_paper-agent_paper-agent__paper_show"
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

```
找到 N 篇相关论文：

1. **[标题]** — 评分 X.X/10
   [一句话描述核心贡献]

2. **[标题]** — 评分 X.X/10
   [一句话描述]

需要查看某篇的详细信息吗？
```
