---
description: "Paper Agent — unified entry point for all research paper workflows"
allowed-tools: [
  "mcp__paper-agent__paper_profile",
  "mcp__paper-agent__paper_stats",
  "mcp__paper-agent__paper_workspace_context"
]
---

# Paper Agent

Unified entry point — help the researcher decide what to do.

## Process

1. Silently call `paper_workspace_context()` + `paper_stats()` to understand the current state
2. Present a personalized menu based on state:

   **Paper Agent** — 你的研究助手

   当前状态：[库中 N 篇论文 | 待读 X | 阅读中 Y]

   ### Slash 命令

   **研究工作流**

   | # | 功能 | 说明 | 命令 |
   |---|------|------|------|
   | 1 | 每日推荐 | 收集今日论文 + 个性化推荐 | `/start-my-day` |
   | 2 | 搜索论文 | 关键词搜索本地库 | `/paper-search <关键词>` |
   | 3 | 深度分析 | 单篇论文结构化分析 | `/paper-analyze <ID>` |
   | 4 | 文献综述 | 一个方向的论文梳理 | `/paper-survey <主题>` |
   | 5 | 趋势分析 | 研究方向热度和趋势 | `/paper-insight <方向>` |
   | 6 | 批量筛选 | 自动分流待读论文 | `/paper-triage` |
   | 7 | 论文对比 | 多篇论文横向对比 | `/paper-compare` |
   | 8 | 下载 PDF | 下载论文全文 | `/paper-download <ID>` |

   **配置与采集**

   | # | 功能 | 说明 | 命令 |
   |---|------|------|------|
   | 9 | 配置研究方向 | 对话式设定 topics / keywords / sources | `/paper-setup` |
   | 10 | 采集论文 | 三源并行抓取 + LLM 评分 | `/paper-collect [天数]` |

   ### 自然语言触发

   不用记命令，直接说需求，我会自动路由到对应的工作流：

   | 你说的话 | 触发的能力 | 背后的 Skill / 工具 |
   |---------|----------|-------------------|
   | "今天看什么" / "start my day" | 每日推荐 | `paper_morning_brief` 一步完成 |
   | "搜一下 GNN placement" | 搜索论文 | `paper_search` / `paper_quick_scan` |
   | "分析这篇" / 给出 arXiv ID | 深度分析 | deep-dive skill |
   | "这个方向有什么工作" / "综述" | 文献综述 | literature-survey skill |
   | "这个方向火不火" / "趋势" | 趋势分析 | research-insight skill |
   | "筛一下" / "哪些值得看" | 批量筛选 | `paper_auto_triage` 一步完成 |
   | "引用链" / "谁引了这篇" | 引用追踪 | `paper_citation_trace` 一步完成 |
   | "帮我找 Attention Is All You Need" | 精确查找 + 下载 | `paper_find_and_download` |
   | "收集论文" / "配置方向" | 采集 / 设置 | `/paper-collect` / `/paper-setup` |

   直接告诉我你想做什么，或输入上面的命令。

3. If user hasn't configured profile yet, skip the menu and guide through setup first
4. If library is empty, suggest starting with `/start-my-day` or `/paper-collect`
5. Route to the selected workflow — for skills, read the corresponding `.claude/skills/<name>/SKILL.md`
