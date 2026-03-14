---
name: citation-explore
description: Explore citation chains via Semantic Scholar — forward and backward citations with recursive tracing. Use when user says "引用链", "citations", "这篇引用了什么", "谁引用了它", "追踪引用", "citation trace", or wants to understand a paper's academic context.
version: 0.2.0
---

# Citation Explore — 引用链探索

从一篇论文出发，递归追踪引用关系，发现关键前置工作和最新进展。

## 交互流程

### Phase 1: 起点确认

**工具**: `paper_show(paper_id)`

呈现论文基本信息后，**必须询问用户**：

> 🗣️ 要查哪个方向的引用？
> a) 它引用了什么（backward） — 找前置工作、理论基础
> b) 谁引用了它（forward） — 找后续改进、最新进展
> c) 双向都查（推荐）

> 🗣️ 每个方向查多少篇？（默认 20）

### Phase 2: 首层查询

**工具**: `paper_citations(paper_id, direction, limit, trace_name)`

呈现引用列表后，**必须询问用户**：

> 🗣️ 引用关系查询完成：
> - 引用了 {n} 篇（backward）
> - 被 {n} 篇引用（forward）
> - 新发现论文 {n} 篇已自动入库
>
> 要深入追踪哪篇？（给编号）
> 还是到此为止？

### Phase 3: 递归追踪（可多轮）

如果用户选择深入：

**工具**: `paper_citations(选中的论文 ID, direction)`

每次追踪后：

> 🗣️ 第 {n} 层追踪完成。要继续追踪吗？
> - 给编号继续深入
> - "够了" 停止追踪

最多建议追踪 3 层，超过 3 层主动提醒：

> 🗣️ 已经追踪了 3 层，引用链可能开始发散了。建议在此整理。继续还是停？

### Phase 4: 整理

**必须询问用户**：

> 🗣️ 探索结束。要做什么？
> a) 创建分组 — 把发现的论文整理成一个分组
> b) 标记待读 — 选几篇标记为待读
> c) 两个都要
> d) 直接看报告

如果选了 a/c：

> 🗣️ 分组叫什么名字？（默认：{trace_name}）

**工具**: `paper_group_create(name)` + `paper_group_add(name, paper_ids)`
**工具**: `paper_reading_status(选中的 IDs, "to_read")`

### Phase 5: 交付件

**必须询问用户**：

> 🗣️ 要保存引用图谱报告吗？
> 默认保存到：`.paper-agent/citation-traces/{trace_name}.md`
> （引用链追踪过程中已自动保存，此处是确认最终版本）

使用 [citation-map-template](references/citation-map-template.md) 生成最终报告。

## 涉及的 MCP 工具

| 工具 | 阶段 | 用途 |
|------|------|------|
| `paper_show` | Phase 1 | 确认起点论文 |
| `paper_citations` | Phase 2-3 | 查询引用关系（递归） |
| `paper_group_create` | Phase 4 | 创建分组 |
| `paper_group_add` | Phase 4 | 添加论文到分组 |
| `paper_reading_status` | Phase 4 | 标记待读 |

## 可跳转的 Skill

- 想深入分析某篇 → **deep-dive**
- 发现的论文太多需要筛选 → **paper-triage**
- 想基于引用链写综述 → **literature-survey**
