---
name: research-insight
description: Research trend analysis and insight generation — method evolution, hot topics, key teams, research gaps. Use when user says "趋势", "洞察", "insight", "这个方向的发展", "什么方法在兴起", "研究热点", "trend analysis", or wants to understand the landscape of a research area.
version: 0.2.0
---

# Research Insight — 研究趋势洞察

分析某个研究方向的趋势、演进、关键团队和研究空白，产出结构化洞察报告。

## 交互流程

### Phase 1: 洞察范围

**必须依次询问用户**：

> 🗣️ 你想了解哪些方向的趋势？
> （可以是一个大方向，也可以列出几个子方向）

> 🗣️ 关注哪些会议/期刊？
> a) 通用 AI 顶会（NeurIPS, ICML, ICLR）
> b) EDA/硬件（DAC, ICCAD, DATE, ISPD）
> c) 自定义: ___
> d) 不限

> 🗣️ 时间范围？
> a) 最近 1 年 — 看最新动态
> b) 最近 3 年 — 看中期趋势（推荐）
> c) 最近 5 年 — 看长期演进
> d) 自定义: ___

> 🗣️ 你最关注什么？（可多选，这决定报告的重点章节）
> a) 方法演进趋势 — 什么方法在兴起、什么在衰落
> b) 热门主题变化 — topic 频率变化
> c) 关键团队与人物 — 谁在做、谁做得好
> d) 研究空白与机会 — 什么还没人做
> e) 产业落地情况 — 哪些方法已商用
> f) 全部
> g) 自定义: ___

### Phase 2: 数据收集

根据 Phase 1 的范围，拆分搜索策略：

**工具**: `paper_search_batch(queries_by_year_and_direction, diverse=True)`
— 按年份 × 方向拆分 queries，获取本地数据

**工具**: `paper_search_online(query)` — 按方向补充在线数据

**工具**: `paper_stats()` — 获取库内统计

呈现收集结果：

> 🗣️ 数据收集完成：
> - {方向 A}: {n} 篇（{year1}: {n}, {year2}: {n}, ...）
> - {方向 B}: {n} 篇
> - 总计: {n} 篇
>
> 数据够做分析吗？要补充搜索吗？

### Phase 3: 分析与呈现

根据用户在 Phase 1 选择的关注维度，使用 [insight-template](references/insight-template.md) 生成洞察报告。

**关键规则**：
- 只展开用户选择的维度，未选的维度用一句话带过或省略
- 趋势判断必须有数据支撑（论文数量、引用次数）
- 新兴方向必须给出具体的代表性论文

### Phase 4: 深入探索

**必须询问用户**：

> 🗣️ 洞察报告草稿完成。你想：
> a) 深入看某个趋势 — 告诉我哪个
> b) 追踪某个方法的引用链 → 切换到 **citation-explore**
> c) 某个方向做个综述 → 切换到 **literature-survey**
> d) 修改报告 — 哪里需要改
> e) 满意，保存报告

### Phase 5: 交付件

**必须询问用户**：

> 🗣️ 保存洞察报告吗？
> - 报告文件：`insight/{topic}-{YYYY-MM-DD}.md`（默认）
> - 要把发现的高影响力论文标记为"待读"吗？
> - 要创建一个 "{topic}-insight" 分组吗？

**工具**:
- 写入报告文件
- `paper_reading_status(high_impact_ids, "to_read")` 或 `"important"`
- `paper_group_create(topic)` + `paper_group_add(topic, ids)`

## 涉及的 MCP 工具

| 工具 | 阶段 | 用途 |
|------|------|------|
| `paper_search_batch` | Phase 2 | 按年份×方向批量搜索 |
| `paper_search_online` | Phase 2 | 在线补充数据 |
| `paper_stats` | Phase 2 | 库统计 |
| `paper_profile` | Phase 3 | 对齐用户研究方向 |
| `paper_batch_show` | Phase 3 | 获取论文详情 |
| `paper_citations` | Phase 4 | 引用链追踪 |
| `paper_reading_status` | Phase 5 | 标记阅读状态 |
| `paper_group_create` | Phase 5 | 创建分组 |
| `paper_group_add` | Phase 5 | 添加到分组 |

## 可跳转的 Skill

- 深入某个趋势的引用链 → **citation-explore**
- 某个方向做综述 → **literature-survey**
- 筛选高影响力论文 → **paper-triage**
- 深入分析某篇 → **deep-dive**
