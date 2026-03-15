---
name: daily-reading
description: Morning paper reading workflow. Triggers on "start my day", "今天看什么", "morning digest", "每日推荐".
---

# Daily Reading

## Flow

1. Call `paper_morning_brief(days=1)` — this single tool does context recovery + collect + digest + auto-mark in one call
2. Call `paper_watch_digest()` — check for watchlist updates
3. Present as structured tables:

   **今日推荐** (N 篇):
   | # | 标题 | 评分 | 关键词 | 一句话总结 |

   **Watchlist 更新** (if any):
   | 跟踪项 | 类型 | 新论文数 | 最相关论文 |

   **结论与建议**: 今日最值得关注的方向和论文，建议阅读顺序

4. **Auto-save**: call `paper_save_report(report_type="daily_digest", content=<digest markdown>, filename="{YYYY-MM-DD}.md")` using the daily-digest-template. Tell user the saved path.
5. **[FORK]** "今日摘要已保存至 {path}。深入看哪篇？还是先这样？"

## If user picks a paper

Hand off to the **deep-dive** skill with the selected paper ID.

## Workspace behavior

The `paper_morning_brief` response includes a `mode` field:
- `"workspace"`: top picks were auto-marked as `to_read`.
  - If `auto_marked` > 0 AND this is the user's first time seeing auto-marking (no prior reading stats), explain: "（首次自动标记）我把 N 篇高相关论文自动标记为'待读'，方便你追踪阅读进度。这个行为可以通过切换到 lightweight 模式关闭。"
  - On subsequent uses, just briefly mention: "已自动标记 N 篇为待读。"
- `"lightweight"`: just present the digest, no status talk.

## Rules

- Only 1 checkpoint (the fork above). Everything else is automatic.
- Don't ask about collection parameters, source selection, or date ranges unless user specifies.
- If digest is empty (no new papers), say so and suggest `paper_quick_scan` for a topic.
