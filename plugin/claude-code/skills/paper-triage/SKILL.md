---
name: paper-triage
description: Batch paper screening and classification. Triggers on "筛一下", "triage", "哪些值得看", "帮我筛", "batch screen".
---

# Paper Triage

## Flow

1. **Context carry-over**:
   - If user explicitly references existing papers ("筛一下刚才的", "帮我筛这些", "筛这些"): triage those directly → `paper_auto_triage(paper_ids=[...])`
   - If papers in context but reference is ambiguous: ASK "要筛选刚才找到的这些论文？还是筛选库里最近的未读论文？"
   - If no context → default to `paper_auto_triage(top_n=5)`
2. **Credibility check**: For papers in the "important" bucket, call `paper_credibility_batch(important_ids)` to add credibility signals.
3. Present the three buckets as tables:

   **重要**: | # | 标题 | 评分 | 入选理由 | venue | code | 复现风险 |
   **待读**: | # | 标题 | 评分 | 简评 |
   **跳过**: | # | 标题 | 评分 | 跳过理由 |
   **结论**: 为什么这几篇最值得关注，关联用户 profile 说明

3. **[FORK]** "这是按你 profile 的分类，同意吗？要调整哪些？"

## If user adjusts

Move papers between buckets per user's instruction, then:
- Call `paper_reading_status(important_ids, "important")` for confirmed important papers
- Call `paper_reading_status(to_read_ids, "to_read")` for to_read papers

## If user confirms as-is

Apply the auto-triage result directly:
- Mark important papers as "important"
- Mark to_read papers as "to_read"
- Skip papers get no status change

After marking, **auto-save**: call `paper_save_report(report_type="triage", content=<report markdown>, filename="{topic}-{YYYY-MM-DD}.md")` using triage-template.

**[CONTEXT-AWARE FORK]** — Based on the triage result, suggest next steps:

- If important bucket has papers with PDFs available:
  "已标记完成，筛选报告已保存至 {path}。\n💡 **下一步建议**：\n1. 批量下载 {N} 篇重要论文的 PDF\n2. 深入分析 [{top_important_title}]（{score}分）\n（说编号或告诉我你想做什么）"

- If important bucket has papers but no PDFs:
  "已标记完成，筛选报告已保存至 {path}。\n💡 **下一步建议**：\n1. 深入分析 [{top_important_title}]（{score}分）\n2. 搜索并下载这些论文的 PDF\n（说编号或告诉我你想做什么）"

- If important bucket is empty but to_read has papers:
  "没有特别突出的论文，但有 {N} 篇值得一读。\n💡 **下一步建议**：\n1. 看看 [{top_to_read_title}] — 评分最高的待读论文\n2. 换个方向搜索\n（说编号或告诉我你想做什么）"

- If all papers are skip:
  "这批论文跟你方向关联不大。\n💡 **下一步建议**：\n1. 调整 research profile — 可能关键词需要更新\n2. 换个方向搜索\n（说编号或告诉我你想做什么）"

## Custom source

If user provides specific paper IDs or says "筛这些":
- Call `paper_auto_triage(paper_ids=[...])` with the specific IDs

## Rules

- Only 1 checkpoint (confirm/adjust). Classification is automatic via `paper_auto_triage`.
- Don't ask about criteria — use profile-based relevance scores by default.
- Don't ask about source — default to recent unread papers.
- Always use tables, never bullet-point lists for paper results.
- Always include a 结论 section explaining why the classification matters.
- FORK suggestions must reference actual paper titles and counts from the triage result.
