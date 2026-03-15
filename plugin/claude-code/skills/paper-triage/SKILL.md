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

**[FORK]** "已标记完成，筛选报告已保存至 {path}。要深入看哪篇？还是先这样？"

## Custom source

If user provides specific paper IDs or says "筛这些":
- Call `paper_auto_triage(paper_ids=[...])` with the specific IDs

## Rules

- Only 1 checkpoint (confirm/adjust). Classification is automatic via `paper_auto_triage`.
- Don't ask about criteria — use profile-based relevance scores by default.
- Don't ask about source — default to recent unread papers.
- Always use tables, never bullet-point lists for paper results.
- Always include a 结论 section explaining why the classification matters.
