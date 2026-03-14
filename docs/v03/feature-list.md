# v03 Feature List — Capability Sinking & Interaction Refinement

> Version: v03
> Theme: 将多步 AI 链、分类逻辑、递归 API 调用、数据聚合下沉为原子后端工具；交互从 ~23 checkpoint 降至 ~7

## 新增 MCP 工具 (5)

| FEAT-ID | 工具名 | 替代什么 | 本质 |
|---------|--------|---------|------|
| FEAT-301 | `paper_quick_scan` | survey/insight 的 3 步 AI 链 (search_batch → search_online → 人工合并去重) | 数据管道 |
| FEAT-302 | `paper_auto_triage` | triage skill 的 "AI 逐篇分析按三档分流" | 基于已有 score 的排序分桶 |
| FEAT-303 | `paper_citation_trace` | citation-explore 的多轮递归 (AI 调 N 次 paper_citations) | API 递归循环 |
| FEAT-304 | `paper_morning_brief` | daily-reading 的 3 次调用链 (workspace_context → collect → digest) | 顺序 I/O 编排 |
| FEAT-305 | `paper_trend_data` | insight skill 的 "AI 脑算" 论文分布趋势 | 纯数据聚合 |

## 增强现有工具 (3)

| FEAT-ID | 工具名 | 增强内容 |
|---------|--------|---------|
| FEAT-306 | `paper_group_add` | 新增 `create_if_missing` 参数，一步建组+加论文 |
| FEAT-307 | `paper_note_add` | 新增 `mark_as` 参数，附带标记阅读状态 |
| FEAT-308 | `paper_workspace_context` | 返回 `mode` 字段 ("workspace"/"lightweight") |

## Skill 行为重构

| FEAT-ID | 内容 |
|---------|------|
| FEAT-309 | 7 个 SKILL.md 重写：fork-only checkpoint、quick-first default、persona annotation |
| FEAT-310 | _skill_content.py + setup.py 分发机制更新 |
| FEAT-311 | 文档更新 (USER-JOURNEY.md, plugin/README.md, README.md) |

## 设计原则

- **Sink data work**: 链式调用、分类、聚合、递归 → 单个后端工具
- **Fork-only**: 只在真正的分叉决策点暂停 (max 2-3 选项)
- **Opt-in deliverables**: 结果内联展示，文件仅在用户明确要求时保存
- **Quick-first**: 默认轻量扫描，完整模式需明确请求
- **Concise choices**: 永远不列超过 3 个选项
- **Persona inference**: 后端检测 workspace/lightweight 用户，不问
