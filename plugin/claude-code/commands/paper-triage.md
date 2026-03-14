---
description: Batch paper screening — auto-classify into important/to_read/skip
allowed-tools: [
  "mcp__paper-agent__paper_auto_triage",
  "mcp__paper-agent__paper_reading_status"
]
---

# Paper Triage

Batch screening of papers using profile-based relevance scores.

## Process

1. Call `paper_auto_triage(top_n=5)` — classifies recent unread papers automatically
2. Present three buckets with scores and reasons
3. **ASK**: "这是按你 profile 的分类，同意吗？要调整哪些？"
4. Apply status marks per user's confirmation/adjustment
5. **ASK**: "已标记完成。要保存筛选报告？还是先这样？"
