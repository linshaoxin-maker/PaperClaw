# v04-experience — 假设登记表

**Phase:** Phase 1
**Last Updated:** 2026-03-15

---

| ASM-ID | 假设 | 影响 | 确认状态 | 确认计划 |
|--------|------|------|---------|---------|
| ASM-V4-01 | LLM 能在单次调用中稳定评估 5 篇论文并返回结构化 JSON（每篇含 score/band/reason/topics） | Batch scoring 可行性；如不成立需保持逐篇模式 | 待确认 | 用 3 篇/批试跑 10 次，检查输出格式一致性和 score 质量 |
| ASM-V4-02 | S2 openAccessPdf URL 对收录论文的有效率 ≥ 50%（URL 存在且可下载） | 下载成功率提升幅度；如有效率 < 30% 则提升有限 | 待确认 | 对本地库 100 篇含 S2 pdf_url 的论文统计 |
| ASM-V4-03 | Feedback 权重偏移 ±1.0 分足以影响排序但不导致推荐漂移 | 偏移太大→推荐不稳定；偏移太小→用户感知不到变化 | 待确认 | 模拟 feedback 后对比前后 digest 排序 |
| ASM-V4-04 | Title 预过滤（keywords 匹配）假阴率 < 5%（不误杀相关论文） | 如假阴率高→评分覆盖不完整，用户错过重要论文 | 待确认 | 200 篇人工标注 relevant/irrelevant 对比预过滤结果 |
| ASM-V4-05 | Skill 文件中的条件分支（"IF 有 PDF → parse → extract"）AI IDE 能稳定执行 | 如执行不稳定→条件分支退化为纯文本建议 | 倾向成立 | Cursor + Claude Code 端到端测试 |
| ASM-V4-06 | `_format_paper()` 新增字段后 digest 可读性不下降 | 信息过多→反而难以浏览 | 待确认 | 格式设计审查 + 实际 digest 效果评估 |
