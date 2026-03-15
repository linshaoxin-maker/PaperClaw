---
name: citation-explore
description: Citation chain exploration. Triggers on "引用链", "谁引了", "citation", "参考文献", "这篇引了谁".
---

# Citation Exploration

## Flow

1. **Resolve paper_id from context**: If the user says "看引用链" without specifying a paper, use the paper currently being discussed in this conversation. If the user refers to a paper by index (e.g. "第2篇的引用链"), resolve from context. If explicit ID given, use that.
2. Call `paper_citation_trace(paper_id, direction="both", max_depth=2)` — traces 2 levels automatically
2. Present results as a tree + key nodes table:

   **引用树**: seed → level 1 → level 2 (text tree)
   **关键节点**: | 论文 | 年份 | 方向 | 被引 | 关系 |
   **结论**: 哪些是领域关键节点，引用链揭示了什么研究脉络
3. **Auto-save**: call `paper_save_report(report_type="citation_map", content=<citation tree markdown>, filename="{seed_id}.md")` to persist the citation map.

4. **[CONTEXT-AWARE FORK]** — Based on the citation trace result, suggest next steps:

   - If found high-citation key nodes:
     "引用图谱已保存至 {path}（发现 {N} 个关键节点）。\n💡 **下一步建议**：\n1. 深入分析关键节点 [{key_node_title}]（{citations} 次引用）\n2. 把这 {N} 篇加到阅读分组 — 方便后续追踪\n（说编号或告诉我你想做什么）"

   - If found recent follow-up papers (last 1-2 years):
     "引用图谱已保存至 {path}。\n💡 **下一步建议**：\n1. 看看最新的跟进工作 [{recent_paper_title}]（{year}）\n2. 基于引用链做这个方向的综述\n（说编号或告诉我你想做什么）"

   - If citation chain is thin (few citations):
     "引用图谱已保存至 {path}。引用链比较短，这可能是个较新的方向。\n💡 **下一步建议**：\n1. 搜索 [{seed_method}] 相关的更多论文\n2. 看看这个方向的趋势分析\n（说编号或告诉我你想做什么）"

## If user picks a paper to trace further

Call `paper_citation_trace(new_paper_id)` again for the selected paper.

## If user wants to group

Call `paper_group_add(name="citation-{seed_title}", paper_ids=[...], create_if_missing=True)`.

## If user wants BibTeX export

Call `paper_export(paper_ids, format="bibtex")` for references.

## Rules

- Only 1 checkpoint. The recursive trace is handled by `paper_citation_trace` in one call.
- Don't ask about direction (both by default) or depth unless user specifies.
- Present the tree concisely: title + year + direction for each paper.
- If workspace mode, mention discovered papers were saved to library.
- FORK suggestions must reference actual key node titles, citation counts, and years from the trace result.
