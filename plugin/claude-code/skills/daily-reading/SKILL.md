---
name: daily-reading
description: Morning paper reading workflow. Triggers on "start my day", "今天看什么", "morning digest", "每日推荐".
---

# Daily Reading

## Flow

1. Call `paper_morning_brief(days=1)` — this single tool does context recovery + collect + digest + auto-mark in one call
2. Present as structured table:

   **今日推荐** (N 篇):
   | # | 标题 | 评分 | 关键词 | 一句话总结 |
   **结论与建议**: 今日最值得关注的方向和论文，建议阅读顺序

3. **[FORK]** "深入看哪篇？保存今日摘要？还是先这样？"

## If user picks a paper

Hand off to the **deep-dive** skill with the selected paper ID.

## If user wants to save

Write the digest to `daily/{YYYY-MM-DD}.md` using the daily-digest-template.

## Workspace behavior

The `paper_morning_brief` response includes a `mode` field:
- `"workspace"`: top picks were auto-marked as `to_read`. Mention this.
- `"lightweight"`: just present the digest, no status talk.

## Rules

- Only 1 checkpoint (the fork above). Everything else is automatic.
- Don't ask about collection parameters, source selection, or date ranges unless user specifies.
- If digest is empty (no new papers), say so and suggest `paper_quick_scan` for a topic.
