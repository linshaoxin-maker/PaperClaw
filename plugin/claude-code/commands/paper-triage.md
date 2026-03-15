---
description: Batch paper screening — auto-classify into important/to_read/skip
allowed-tools: [
  "mcp__paper-agent__paper_auto_triage",
  "mcp__paper-agent__paper_reading_status",
  "mcp__paper-agent__paper_credibility_batch",
  "mcp__paper-agent__paper_save_report",
  "mcp__paper-agent__paper_show",
  "Read"
]
---

# Paper Triage

> Workflow detail: read `.claude/skills/paper-triage/SKILL.md` for classification rules, custom source handling, and save report format.

Batch screening of papers using profile-based relevance scores.

## Process

1. **Context carry-over**:
   - If user explicitly references existing papers ("筛一下刚才的", "帮我筛这些"): triage those directly → `paper_auto_triage(paper_ids=[...])`
   - If papers in context but reference is ambiguous: ASK "要筛选刚才找到的这些论文？还是筛选库里最近的未读论文？"
   - If no context → default to `paper_auto_triage(top_n=5)`
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
5. **Auto-save**: call `paper_save_report(report_type="triage", content=<report markdown>, filename="{topic}-{YYYY-MM-DD}.md")` to persist the triage report
6. Tell user: "📄 筛选报告已保存至 {path}。要深入看哪篇？"
