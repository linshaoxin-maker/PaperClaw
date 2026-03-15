---
description: "Paper Agent — unified entry point for all research paper workflows"
allowed-tools: [
  "mcp__paper-agent__paper_profile",
  "mcp__paper-agent__paper_profile_update",
  "mcp__paper-agent__paper_stats",
  "mcp__paper-agent__paper_workspace_context",
  "mcp__paper-agent__paper_morning_brief",
  "mcp__paper-agent__paper_quick_scan",
  "mcp__paper-agent__paper_auto_triage",
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_show",
  "mcp__paper-agent__paper_batch_show",
  "mcp__paper-agent__paper_citation_trace",
  "mcp__paper-agent__paper_trend_data",
  "mcp__paper-agent__paper_compare",
  "mcp__paper-agent__paper_note_add",
  "mcp__paper-agent__paper_reading_status",
  "mcp__paper-agent__paper_collect",
  "mcp__paper-agent__paper_download",
  "mcp__paper-agent__paper_find_and_download",
  "mcp__paper-agent__paper_export",
  "mcp__paper-agent__paper_group_add",
  "mcp__paper-agent__paper_sources_list",
  "mcp__paper-agent__paper_sources_enable",
  "mcp__paper-agent__paper_templates_list",
  "mcp__paper-agent__paper_health",
  "mcp__paper-agent__paper_save_report",
  "mcp__paper-agent__paper_list_reports",
  "Read",
  "Write"
]
---

# Paper Agent

Unified entry point — understand user state, recommend actions, and execute in the same turn.

## Process

1. Silently call `paper_workspace_context()` + `paper_stats()` to understand the current state
2. Based on state, show **top 3 recommended actions** (not the full command list):

   **New user** (no profile):
   > 看起来你是第一次用 Paper Agent！我先帮你设置研究方向，这样才能给你个性化的推荐。
   > 告诉我你的研究领域和关注的方向？

   **Empty library** (profile exists, 0 papers):
   > 研究方向已配好，论文库还是空的。建议：
   > 1. **今日推荐** — 收集并推荐最新论文（`/start-my-day`）
   > 2. **搜索论文** — 搜一个你关注的主题
   > 3. **采集论文** — 批量抓取最近一周的论文

   **Has unread papers** (to_read > 0):
   > 你有 N 篇待读论文。建议：
   > 1. **批量筛选** — 帮你自动分出最值得读的（`/paper-triage`）
   > 2. **今日推荐** — 看看今天有没有新论文
   > 3. **搜索论文** — 找特定方向的论文
   >
   > 输入"查看全部功能"展示完整命令列表。你也可以直接说你想做什么。

   **Returning user** (has reading history):
   > 当前状态：库中 N 篇论文 | 待读 X | 阅读中 Y
   > 建议：
   > 1. **今日推荐** — 看看有没有新论文
   > 2. **继续阅读** — 你有 Y 篇正在读
   > 3. **文献综述** / **趋势分析** — 对某个方向做系统梳理
   >
   > 输入"查看全部功能"展示完整命令列表。你也可以直接说你想做什么。

3. **If user says "查看全部功能" or "show all"**, then show the full table:

   | # | 功能 | 说明 | 命令 / 说法 |
   |---|------|------|------------|
   | 1 | 每日推荐 | 收集 + 推荐 | `/start-my-day` 或 "今天看什么" |
   | 2 | 搜索论文 | 关键词搜索 | `/paper-search` 或 "搜一下 X" |
   | 3 | 深度分析 | 单篇分析 | `/paper-analyze` 或 "分析这篇" |
   | 4 | 文献综述 | 方向梳理 | `/paper-survey` 或 "综述" |
   | 5 | 趋势分析 | 热度趋势 | `/paper-insight` 或 "这个方向火不火" |
   | 6 | 批量筛选 | 自动分流 | `/paper-triage` 或 "筛一下" |
   | 7 | 论文对比 | 横向对比 | `/paper-compare` 或 "对比这几篇" |
   | 8 | 下载 PDF | 论文全文 | `/paper-download` 或给 arXiv ID |
   | 9 | 引用追踪 | 引用网络 | "引用链" 或 "谁引了这篇" |
   | 10 | 配置方向 | 设定 profile | `/paper-setup` |
   | 11 | 采集论文 | 批量抓取 | `/paper-collect` |
   | 12 | 健康检查 | 诊断安装 | "检查一下" 或 call `paper_health` |

4. **If user directly states intent** (e.g. "今天看什么", "搜 GNN 的论文"), skip the menu and **execute immediately** using the tools above. This is the key difference from a menu — /paper can route AND execute.
5. For multi-step workflows, read `.claude/skills/<name>/SKILL.md` for the full flow.
