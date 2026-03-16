# Paper Agent v04-experience — Idea Brief

**Phase:** Phase 0 (想法澄清)
**Status:** Draft
**Last Updated:** 2026-03-15

---

## 1. 问题陈述

Paper Agent 自 v01 至 v03 已经实现了从论文采集到研究规划的完整工具链（50+ MCP 工具），但存在一个关键矛盾：

**系统能力 >> 用户可感知能力**

具体表现：
1. 6 个 Workflow Skills 仍引用 v02 工具集（~15 个），v03-v06 的 35+ 工具无 Skill 引导
2. 输出报告（digest、analysis、survey）缺少结构化数据支撑，AI 自由填充导致质量不稳定
3. LLM scoring 逐篇串行，200 篇论文评分耗时过长
4. 反馈学习和 watchlist 有工具但无闭环——记录了偏好但不影响推荐
5. PDF 下载只支持 arXiv，非 arXiv 论文（~50% 的会议论文）无法下载
6. Paper 序列化接口遗漏了研究者最关心的字段（被引数、阅读状态、arXiv ID）

## 2. 目标

| 目标 | 量化成功标准 |
|------|------------|
| 能力可达性 | Router Skill 意图映射覆盖 ≥90% 的已有工具 |
| 输出质量 | Digest/Survey/Insight 报告中硬数据字段 ≥ 模板字段的 60%（当前 ~20%） |
| Scoring 性能 | 200 篇论文 scoring 时间 ≤ 原来的 40% |
| 反馈闭环 | 用户标记 "relevance_override" 后，下次 digest 中同类论文排序可见变化 |
| 下载成功率 | PDF 下载成功率从 ~50% 提升到 ≥ 75% |
| 信息密度 | `to_summary_dict()` 新增 ≥ 3 个关键字段 |

## 3. 非目标

- 不新增 MCP 工具（工具已足够，问题在 Skill 层和体验层）
- 不引入 embedding / 向量搜索（延后到 v05）
- 不做 Survey 增量更新（延后到 v05）
- 不做 Web UI
- 不改变架构分层（ADR-003 的数据层+交互层分离维持不变）

## 4. 风险与假设

| ID | 假设/风险 | 影响 | 缓解措施 |
|---|---------|------|---------|
| ASM-V4-01 | Batch scoring prompt 可以在单次 LLM 调用中稳定评估 5-8 篇论文 | 性能优化是否可行 | 先用 3 篇/批验证，渐进增大 |
| ASM-V4-02 | S2 openAccessPdf URL 可用率足够高 | 下载成功率提升幅度 | 保留 arXiv 优先策略，S2 作 fallback |
| ASM-V4-03 | Feedback 权重调整不会导致推荐结果"漂移"过度 | 推荐质量稳定性 | 设置偏移上限（±2.0），加入衰减机制 |
| ASM-V4-04 | Skill 文件的条件分支逻辑 AI IDE 能正确执行 | 条件分支可靠性 | 在 Skill 中用明确的 if/then 自然语言指令，避免复杂嵌套 |
| ASM-V4-05 | `_skill_content.py` 与 `plugin/` 目录的内容可以通过手动同步保持一致 | 分发一致性 | OQ-V4-006 中考虑自动化脚本 |
| RISK-V4-01 | Batch scoring 可能导致 LLM 对个别论文评分不如逐篇精确 | 评分质量 | 对 high band (≥7) 的论文提供逐篇 rescore 选项 |
