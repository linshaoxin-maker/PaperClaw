---
name: deep-dive
description: Deep analysis of a single paper — structured analysis, notes, citations, status management. Use when user says "分析这篇论文", "paper-analyze", "深度分析", "展开讲讲", "这篇论文怎么样", or references a specific paper ID for analysis.
version: 0.2.0
---

# Deep Dive — 论文深度分析

对单篇论文进行结构化深度分析，保存笔记，管理阅读状态。

## 交互流程

### Phase 1: 确认论文

**工具**: `paper_show(paper_id)`

呈现论文基本信息后，**必须询问用户**：

> 🗣️ 要从哪些角度分析这篇论文？
> a) 方法创新点 — 核心思想、与前人区别
> b) 实验设计 — benchmark、baseline、指标
> c) 与我研究的关联 — 对我当前工作的启发
> d) 局限与改进空间 — 弱点和可能的改进方向
> e) 全部（推荐首次阅读）

### Phase 2: 生成分析

根据用户选择的角度，使用 [analysis-template](references/analysis-template.md) 生成结构化分析。

**关键**：必须结合用户的 `paper_profile` 研究方向，在"与我研究的关联"部分给出个性化建议。

### Phase 3: 保存与标记

**必须询问用户**：

> 🗣️ 分析完成。接下来：
> 1. 保存笔记吗？（默认保存到 `.paper-agent/notes/{paper_id}.md`）
> 2. 标记为什么状态？
>    - `reading` — 正在读，还没读完
>    - `read` — 读完了
>    - `important` — 重要论文，需要反复参考

**工具**: `paper_note_add(paper_id, content, "ai_analysis")`
**工具**: `paper_reading_status([paper_id], status)`

### Phase 4: 延伸（可选）

**必须询问用户**：

> 🗣️ 要继续做什么？
> a) 查引用链 — 这篇引用了谁、谁引用了它 → 切换到 **citation-explore**
> b) 找相似论文 — 搜索方法/主题相似的论文
> c) 加入分组 — 加到某个论文分组里
> d) 对比 — 跟其他论文做对比
> e) 结束

根据用户选择：
- a → 跳转 **citation-explore** skill
- b → `paper_search(相关关键词, diverse=True)`
- c → `paper_group_add(name, [paper_id])`（如果分组不存在先 `paper_group_create`）
- d → 让用户给其他论文 ID，调用 `paper_compare`

### Phase 5: 交付件

交付件为笔记文件，在 Phase 3 已保存。文件路径：`.paper-agent/notes/{paper_id}.md`

## 涉及的 MCP 工具

| 工具 | 阶段 | 用途 |
|------|------|------|
| `paper_show` | Phase 1 | 获取论文详情 |
| `paper_profile` | Phase 2 | 获取用户研究方向 |
| `paper_note_add` | Phase 3 | 保存分析笔记 |
| `paper_reading_status` | Phase 3 | 标记阅读状态 |
| `paper_citations` | Phase 4 | 查引用链 |
| `paper_search` | Phase 4 | 找相似论文 |
| `paper_group_add` | Phase 4 | 加入分组 |
| `paper_compare` | Phase 4 | 对比论文 |

## 可跳转的 Skill

- Phase 4a → **citation-explore**
- Phase 4d → **literature-survey**（如果要对比的论文多于 3 篇）
