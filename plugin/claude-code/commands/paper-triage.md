---
description: Batch paper screening — auto-classify into important/to_read/skip
allowed-tools: [
  "mcp__paper-agent__paper_auto_triage",
  "mcp__paper-agent__paper_reading_status",
  "Read"
]
---

# Paper Triage

> Workflow detail: read `.claude/skills/paper-triage/SKILL.md` for classification rules, custom source handling, and save report format.

Batch screening of papers using profile-based relevance scores.

## Process

1. Call `paper_auto_triage(top_n=5)` — classifies recent unread papers automatically
2. Present three buckets as tables:

   **⭐ 重要** (N 篇)
   | # | 标题 | 评分 | 入选理由 |
   |---|------|------|---------|

   **📖 待读** (N 篇)
   | # | 标题 | 评分 | 简评 |

   **⏭️ 跳过** (N 篇)
   | # | 标题 | 评分 | 跳过理由 |

   **结论**: 为什么这几篇最值得关注（关联用户 profile 说明）
3. **ASK**: "这是按你 profile 的分类，同意吗？要调整哪些？"
4. Apply status marks per user's confirmation/adjustment
5. **ASK**: "已标记完成。要保存筛选报告？还是先这样？"
