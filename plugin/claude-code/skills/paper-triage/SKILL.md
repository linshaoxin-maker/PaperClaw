---
name: paper-triage
description: Batch paper screening and classification — filter papers by criteria, mark reading status, create groups. Use when user says "帮我筛一下", "triage", "哪些值得读", "分类一下这些论文", "筛选", or has a batch of papers to evaluate.
version: 0.2.0
---

# Paper Triage — 论文筛选分流

对一批论文进行快速筛选，按重要程度分流，批量标记状态。

## 交互流程

### Phase 1: 确定范围

**必须询问用户**：

> 🗣️ 要筛选哪些论文？
> a) 今日推荐的论文
> b) 某次搜索的结果 — 告诉我搜什么
> c) 某个分组里的论文 — 告诉我分组名
> d) 按关键词现搜一批 — 告诉我关键词
> e) 给我一批 paper ID

根据选择获取候选论文列表：
- a → `paper_digest()` 获取推荐
- b → `paper_search(query, diverse=True)`
- c → `paper_group_show(name)`
- d → `paper_search(keywords)` 或 `paper_search_online(keywords)`
- e → `paper_batch_show(paper_ids)`

### Phase 2: 筛选标准

**必须询问用户**：

> 🗣️ 按什么标准筛选？
> a) 跟我研究的相关度 — 基于你的 profile 判断
> b) 方法新颖性 — 关注新方法、新框架
> c) 实验质量 — 关注 benchmark 和结果
> d) 你帮我判断（推荐） — 综合考虑以上全部
> e) 自定义标准: ___

> 🗣️ 需要重点关注什么？（影响筛选偏好）
> - 某个具体方法（如 RL、GNN）
> - 某个应用场景（如 placement、routing）
> - 某个时间段（如最近半年）
> - 无特殊偏好

### Phase 3: AI 筛选建议

**工具**: `paper_profile()` — 获取用户研究方向

AI 逐篇给出建议，按三档分流：

> 🗣️ 我的筛选建议（共 {n} 篇）：
>
> **⭐ 重要（{n} 篇）** — 高度相关，建议精读
> | # | 标题 | 评分 | 入选理由 |
> |---|------|------|---------|
>
> **📖 待读（{n} 篇）** — 值得看，泛读即可
> | # | 标题 | 评分 | 简评 |
> |---|------|------|------|
>
> **⏭️ 跳过（{n} 篇）** — 暂时不需要
> | # | 标题 | 评分 | 跳过理由 |
> |---|------|------|---------|
>
> 同意这个分类吗？要调整哪些？（给编号和新分类）

### Phase 4: 执行操作

用户确认后，批量执行：

**工具**: `paper_reading_status(important_ids, "important")`
**工具**: `paper_reading_status(to_read_ids, "to_read")`

**必须询问用户**：

> 🗣️ 状态已更新。要把"重要"的论文加到某个分组吗？
> a) 创建新分组 — 取什么名？
> b) 加到已有分组 — 哪个？
> c) 不用了

**工具**: `paper_group_create(name)` 或 `paper_group_add(name, ids)`

### Phase 5: 交付件

**必须询问用户**：

> 🗣️ 要保存筛选报告吗？
> 默认保存到：`triage/{topic}-{YYYY-MM-DD}.md`

使用 [triage-template](references/triage-template.md) 生成报告。

## 涉及的 MCP 工具

| 工具 | 阶段 | 用途 |
|------|------|------|
| `paper_digest` / `paper_search` / `paper_group_show` | Phase 1 | 获取候选论文 |
| `paper_batch_show` | Phase 1 | 获取论文详情 |
| `paper_profile` | Phase 3 | 获取用户研究方向 |
| `paper_reading_status` | Phase 4 | 批量标记状态 |
| `paper_group_create` | Phase 4 | 创建分组 |
| `paper_group_add` | Phase 4 | 添加到分组 |

## 可跳转的 Skill

- 想深入某篇"重要"论文 → **deep-dive**
- 想基于筛选结果写综述 → **literature-survey**
