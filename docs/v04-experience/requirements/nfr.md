# v04-experience — NFR + 体验指标

**Phase:** Phase 1
**Last Updated:** 2026-03-15

---

## 非功能需求

| NFR-ID | 类别 | 需求 | 量化指标 | 测量方法 |
|--------|------|------|---------|---------|
| NFR-V4-01 | 性能 | Batch scoring 200 篇论文总耗时 ≤ 逐篇模式的 40% | batch_time / serial_time ≤ 0.4 | 基准测试 (同 LLM provider，同 profile) |
| NFR-V4-02 | 性能 | Title 预过滤 200 篇论文 ≤ 500ms | wall clock time | time.perf_counter |
| NFR-V4-03 | 兼容性 | `to_summary_dict()` 新增字段不破坏已有消费者 | 新增字段 value 可为 null | 类型检查 + 已有测试通过 |
| NFR-V4-04 | 兼容性 | Digest markdown 格式变化不破坏 Workspace 文件解析 | WorkspaceManager.rebuild_digest() 正常 | 集成测试 |
| NFR-V4-05 | 可靠性 | Batch scoring 失败 fallback 到逐篇模式成功率 100% | 0 例挂起/死锁 | 异常注入测试 |
| NFR-V4-06 | 可靠性 | PDF 下载 fallback 链每环节超时 ≤ 30s | httpx.Timeout(30) | 超时测试 |
| NFR-V4-07 | 可维护性 | `_skill_content.py` 与 `plugin/` 目录内容一致 | diff 输出为空 | 脚本校验/CI check |

## 体验指标

| UX-ID | 类别 | 指标 | 当前值 | 目标值 | 测量方法 |
|-------|------|------|--------|--------|---------|
| UX-V4-01 | 信息密度 | Digest 每篇论文展示的判断信息字段数 | 3 (score, reason, abstract) | ≥ 6 | Digest 格式审查 |
| UX-V4-02 | 速度 | 200 篇论文 scoring 总耗时 | ~5 min | ≤ 2 min | 计时 |
| UX-V4-03 | 可达性 | 自然语言意图能路由到的 MCP 工具比例 | ~70% (16 个未引用) | ≥ 85% | 意图覆盖率审计 |
| UX-V4-04 | 信任感 | Feedback 后推荐排序变化可感知 | 无变化 | 1 次 digest 内可见 | 前后对比 |
| UX-V4-05 | 完成率 | PDF 下载成功率（混合来源 100 篇） | ~50% | ≥ 75% | 统计 |
