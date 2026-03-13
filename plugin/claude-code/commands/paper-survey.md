---
description: Generate a literature survey from selected papers
argument-hint: <topic>
allowed-tools: [
  "mcp__plugin_paper-agent_paper-agent__paper_search",
  "mcp__plugin_paper-agent_paper-agent__paper_search_online",
  "mcp__plugin_paper-agent_paper-agent__paper_survey_collect",
  "mcp__plugin_paper-agent_paper-agent__paper_batch_show",
  "mcp__plugin_paper-agent_paper-agent__paper_compare",
  "mcp__plugin_paper-agent_paper-agent__paper_export",
  "Write"
]
---

# Paper Survey

Generate a structured literature survey around a research topic.

## Process

1. Parse $ARGUMENTS as the survey topic
2. Analyze the topic — extract keywords, expand search terms, confirm with user
3. Search for papers:
   - `paper_search(query)` for local library
   - If results insufficient, ask user: "本地找到 N 篇，要从 arXiv 在线补充搜索吗？"
   - If yes, `paper_search_online(query)` for additional papers
4. Present candidate list and let user select which to include
5. Ask which sections to include:
   - a) Background & Motivation
   - b) 方法分类与对比
   - c) 实验结果汇总
   - d) Open Problems & Future Directions
   - e) 全部
6. Call `paper_batch_show(selected_ids)` to get full details
7. Generate the survey in Chinese with proper citations
8. Show draft and ask for feedback: "需要修改哪里？"
9. Iterate based on feedback
10. Ask save path and write to file
11. Offer to export BibTeX: `paper_export(ids, format="bibtex")`

## Output Format

Survey should include:
- 引言与背景
- 方法分类 (taxonomy)
- 各方法详解与对比表格
- 实验对比
- 研究空白与未来方向
- 参考文献
