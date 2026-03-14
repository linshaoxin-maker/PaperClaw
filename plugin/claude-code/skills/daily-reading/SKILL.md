---
name: daily-reading
description: Daily research startup workflow — context recovery, paper collection, digest, and triage. Use when user says "start my day", "每日开工", "今天有什么新论文", "开始工作", or any morning research routine trigger.
version: 0.2.0
---

# Daily Reading — 每日开工

每天早上的完整研究启动流程：恢复上下文 → 采集新论文 → 推荐 → 标记状态。

## 交互流程

### Phase 1: 上下文恢复

**工具**: `paper_workspace_context()`

呈现昨日研究活动摘要后，**必须询问用户**：

> 🗣️ 你昨天的进展如上。要：
> a) 先看昨天未完成的待读论文
> b) 直接收集今天的新论文
> c) 两个都要（推荐）

### Phase 2: 采集新论文

**工具**: `paper_collect(days=1)`

呈现采集结果（来源分布、新增/重复数量），然后自动进入推荐。

### Phase 3: 每日推荐

**工具**: `paper_digest()`

呈现推荐列表后，**必须询问用户**：

> 🗣️ 这 {n} 篇推荐中，要标记哪些为待读？（给我编号，或"全部"）
> 有特别重要的吗？我可以直接标记为"重要"。

**工具**: `paper_reading_status(选中的 IDs, status)`

### Phase 4: 深入（可选）

**必须询问用户**：

> 🗣️ 要深入看哪篇？还是先干活了？
> - 给我编号 → 我切换到 **deep-dive** 模式
> - "先干活" → 结束，祝你今天高效！

### Phase 5: 交付件

**必须询问用户**：

> 🗣️ 要保存今天的阅读摘要吗？
> 默认保存到：`daily/{YYYY-MM-DD}.md`

**工具**: 使用 [daily-digest-template](references/daily-digest-template.md) 生成文件

## 涉及的 MCP 工具

| 工具 | 阶段 | 用途 |
|------|------|------|
| `paper_workspace_context` | Phase 1 | 恢复上下文 |
| `paper_collect` | Phase 2 | 采集新论文 |
| `paper_digest` | Phase 3 | 生成推荐 |
| `paper_reading_status` | Phase 3 | 批量标记状态 |
| `paper_reading_stats` | Phase 3 | 展示阅读进度 |

## 可跳转的 Skill

- Phase 4 选择深入 → **deep-dive**
- 想做筛选分流 → **paper-triage**
