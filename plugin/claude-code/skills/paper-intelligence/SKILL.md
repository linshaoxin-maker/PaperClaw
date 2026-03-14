---
name: paper-intelligence
description: AI research paper intelligence — route user intent to the right workflow skill. Use when the user mentions paper, arxiv, digest, research paper, 论文, 论文分析, start my day, paper-analyze, paper-compare, paper-survey, arXiv IDs (like 2301.12345), ML method names, or asks about academic research trends.
version: 0.3.0
---

# Paper Intelligence — 意图路由

这是 paper-agent 的**路由 Skill**。根据用户意图，引导到具体的工作流 Skill。

## 意图路由表

| 用户说了什么 | 路由到 | 说明 |
|------------|--------|------|
| "start my day"、"每日开工"、"今天有什么新论文" | **daily-reading** | 每日启动：上下文恢复→采集→推荐→标记 |
| "分析这篇"、"展开讲讲"、arXiv ID | **deep-dive** | 单篇深度分析→笔记→状态→延伸 |
| "综述"、"survey"、"这个方向有哪些工作" | **literature-survey** | 关键词→搜索→筛选→生成综述→导出 |
| "引用链"、"谁引用了它"、"citations" | **citation-explore** | 双向引用→递归追踪→整理→分组 |
| "帮我筛一下"、"哪些值得读"、"triage" | **paper-triage** | 批量筛选→分流→标记状态→分组 |
| "趋势"、"洞察"、"什么方法在兴起" | **research-insight** | 范围→数据→趋势分析→洞察报告 |

## Skill 之间的跳转

```
daily-reading ──→ deep-dive ──→ citation-explore
      │                │               │
      └→ paper-triage  └→ lit-survey   └→ lit-survey
                              │
research-insight ────→ citation-explore
         │
         └──────────→ literature-survey
```

## 快速 MCP 调用（不需要完整 Skill 流程）

简单的单工具请求不需要走 Skill 流程，直接调用：

| 场景 | 工具 |
|------|------|
| 搜一下某个关键词 | `paper_search` |
| 看某篇论文详情 | `paper_show` |
| 看阅读进度 | `paper_reading_stats` |
| 看分组列表 | `paper_group_list` |
| 下载 PDF | `paper_download` |
| 导出 BibTeX | `paper_export` |

## Output Rules

1. **Chinese first**: All analysis and summaries in Chinese
2. **Wikilink format**: Paper titles as `[[论文标题]]`
3. **Concise by default**: Brief results for search, full detail only for deep analysis
4. **Always ask before acting**: 每个 Skill 的关键节点必须询问用户
5. **Deliverable at the end**: 每个 Skill 结束时询问是否保存交付件
6. **Suggest next skill**: 每个 Skill 结束时建议可能的下一步

## Available Workflow Skills

| Skill | 交付件 | 默认路径 |
|-------|--------|---------|
| [daily-reading](../daily-reading/SKILL.md) | 每日阅读摘要 | `daily/{YYYY-MM-DD}.md` |
| [deep-dive](../deep-dive/SKILL.md) | 论文分析笔记 | `.paper-agent/notes/{paper_id}.md` |
| [literature-survey](../literature-survey/SKILL.md) | 综述 + BibTeX | `survey/{topic}.md` + `.bib` |
| [citation-explore](../citation-explore/SKILL.md) | 引用图谱 | `.paper-agent/citation-traces/{name}.md` |
| [paper-triage](../paper-triage/SKILL.md) | 筛选报告 | `triage/{topic}-{date}.md` |
| [research-insight](../research-insight/SKILL.md) | 洞察报告 | `insight/{topic}-{date}.md` |
