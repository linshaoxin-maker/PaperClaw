## Feature 验证报告：FEAT-V4-04 Title 预过滤

### 1. 四可检验验收
| 检验项 | 验收结论 | 说明 |
|---|---|---|
| 可感知 | ✅ | 评分速度进一步提升 + 日志中可见 pre-filtered 统计 |
| 可演示 | ✅ | 200 篇收集 → 预过滤跳过 N 篇 → LLM 只评其余 |
| 可端到端 | ✅ | 收集 → 预过滤 → batch scoring → digest |
| 可独立上线 | ✅ | 集成在 FilteringManager 中，依赖 FEAT-V4-03（同 Sprint 已完成） |

### 2. 用户感知说明
- 不相关论文（title/abstract 不含 profile keywords 及同义词）直接标记为 score=1.0
- 预过滤可通过配置关闭（pre_filter_enabled=False）
- 日志中有 "Pre-filtered N/M papers, LLM scored K" 统计
- 预过滤使用 search_engine 的 _SYNONYM_GROUPS 扩展同义词覆盖

### 3. 技术验证汇总
| 验证项 | 状态 | 说明 |
|---|---|---|
| 契约符合性 | ✅ | 与 FS-04 一致 |
| 回归测试 | ⚠️ | 需验证假阴率 (ASM-V4-04) |
| 架构守护 | ✅ | 变更限于 FilteringManager._pre_filter() |
