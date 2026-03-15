---
description: Explore citation chains — who cited this paper, what did it cite, find seminal works
argument-hint: <paper_id or arxiv_id>
allowed-tools: [
  "mcp__paper-agent__paper_show",
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_citation_trace",
  "mcp__paper-agent__paper_citations",
  "mcp__paper-agent__paper_batch_show",
  "mcp__paper-agent__paper_note_add",
  "mcp__paper-agent__paper_reading_status",
  "mcp__paper-agent__paper_save_report",
  "mcp__paper-agent__paper_find_and_download",
  "Read",
  "Write"
]
---

# Paper Citation

> Workflow detail: read `.claude/skills/citation-explore/SKILL.md` for full citation exploration rules and output format.

Explore citation chains for a paper.

## Process

1. **Resolve paper_id**: If $ARGUMENTS is a paper ID or arXiv ID, use it directly. If the user refers to a paper by index (e.g. "第2篇的引用链"), resolve from papers discussed earlier in this conversation.
2. Call `paper_citation_trace(paper_id)` to get the citation network
3. Present results as structured tables:

   **被引论文** (Cited by):
   | # | 标题 | 年份 | 引用数 | 关联度 |
   |---|------|------|--------|--------|

   **参考文献** (References):
   | # | 标题 | 年份 | 引用数 | 关联度 |
   |---|------|------|--------|--------|

   **关键发现**: 引用链中的关键节点、研究脉络、seminal works

4. **Auto-save**: call `paper_save_report(report_type="citation_trace", content=<report markdown>, filename="{paper_id}-citations.md")`
5. Tell user: "📄 引用链分析已保存至 {path}。要深入看某篇？还是先这样？"
6. If user picks a paper from the citation chain, call `paper_show(paper_id)` or hand off to deep-dive skill
