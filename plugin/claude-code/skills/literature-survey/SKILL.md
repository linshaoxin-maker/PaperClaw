---
name: literature-survey
description: Generate a structured literature survey — from keyword refinement to final report with BibTeX. Use when user says "综述", "survey", "文献调研", "帮我写个综述", "这个方向有哪些工作", or wants to systematically review a research area.
version: 0.2.0
---

# Literature Survey — 文献综述

从需求澄清到综述成文的完整流程，带交互式论文筛选和迭代修改。

## 交互流程

### Phase 1: 需求澄清

**必须依次询问用户**：

> 🗣️ 综述的主题是什么？

> 🗣️ 要覆盖哪些子方向？我帮你拆关键词。
> （AI 根据主题提出 3-5 组关键词分组）

> 🗣️ 时间范围？
> a) 最近 1 年
> b) 最近 3 年
> c) 最近 5 年（推荐综述用）
> d) 自定义: ___

> 🗣️ 我拆分的关键词如下，覆盖够吗？要调整吗？
> - 方向 A: {keywords}
> - 方向 B: {keywords}
> - 方向 C: {keywords}

### Phase 2: 搜索论文

**工具**: `paper_search_batch(queries, diverse=True)`

呈现各方向命中数后，**必须询问用户**：

> 🗣️ 本地搜索结果：
> - 方向 A: {n} 篇
> - 方向 B: {n} 篇
> - 方向 C: {n} 篇
>
> 本地结果{够/不够}。要从在线源（arXiv + Semantic Scholar）补充吗？

如果用户说要：
**工具**: `paper_search_online(query)` （对每个不足的方向）

### Phase 3: 论文筛选

合并去重，按相关度排序，呈现候选列表。

**必须询问用户**：

> 🗣️ 以下是候选论文（共 {n} 篇），按相关度排序：
>
> | # | 标题 | 年份 | 来源 | 评分 |
> |---|------|------|------|------|
> | 1 | ... | ... | ... | ... |
>
> 要纳入综述的论文？可以给编号（如 1,2,5-10），或"全选"，或"前 N 篇"。

**工具**: `paper_batch_show(选中的 IDs)` — 获取详细信息

### Phase 4: 综述生成

**必须询问用户**：

> 🗣️ 综述包含哪些章节？
> a) Background & Motivation
> b) 方法分类与对比
> c) 实验结果汇总
> d) 研究空白与未来方向
> e) 全部（推荐）
> f) 自定义: ___

> 🗣️ 你最关注的分析维度是什么？（这会影响对比表格的重点）
> - 方法架构差异
> - 实验性能对比
> - 适用场景区分
> - 其他: ___

使用 [survey-template](references/survey-template.md) 生成综述草稿。

### Phase 5: 迭代修改

**必须询问用户**：

> 🗣️ 综述草稿完成（约 {n} 字）。看看哪里需要修改？
> 直到用户说"可以了"才进入下一步。

### Phase 6: 交付件

**必须询问用户**：

> 🗣️ 保存综述吗？
> - 综述文件：`survey/{topic}.md`（默认）
> - BibTeX：需要导出吗？默认 `survey/{topic}-refs.bib`
> - 论文分组：要创建一个 "{topic}" 分组吗？

**工具**:
- 写入综述文件
- `paper_export(paper_ids, "bibtex")` → 写入 .bib 文件
- `paper_group_create(topic)` + `paper_group_add(topic, paper_ids)`

## 涉及的 MCP 工具

| 工具 | 阶段 | 用途 |
|------|------|------|
| `paper_search_batch` | Phase 2 | 多方向批量搜索 |
| `paper_search_online` | Phase 2 | 在线补充搜索 |
| `paper_batch_show` | Phase 3 | 获取论文详情 |
| `paper_compare` | Phase 4 | 方法对比数据 |
| `paper_export` | Phase 6 | 导出 BibTeX |
| `paper_group_create` | Phase 6 | 创建论文分组 |
| `paper_group_add` | Phase 6 | 添加论文到分组 |

## 可跳转的 Skill

- 想深入某篇 → **deep-dive**
- 想看引用链 → **citation-explore**
