# ADR-005: LLM Batch Scoring 策略

## 基本信息
- 状态: accepted
- 日期: 2026-03-15
- 关联: FR-V4-03, NFR-V4-01

## 背景

FilteringManager 当前使用 ThreadPoolExecutor(max_workers=8) 并行评分，每个 worker 做 1 次 LLM 调用评估 1 篇论文。200 篇论文需要 200 次 API 调用，受 LLM provider rate limit 限制，总耗时约 5 分钟。需要减少 API 调用次数。

## 备选方案

| 方案 | 描述 | 优势 | 劣势 |
|---|---|---|---|
| A. 保持逐篇并行 | 维持现状 | 无风险 | 性能已到瓶颈 |
| B. Batch prompt | 一次 prompt 评估 5-8 篇论文 | API 调用减少 75-80%；实现简单 | 单篇评分精度可能微降；JSON 解析风险 |
| C. 两阶段评分 | 先用轻量模型粗筛，再用精确模型精评 | 最优性能 | 需两种 LLM；逻辑复杂；成本可能更高 |

## 决策

选择 **方案 B: Batch prompt**。

## 理由

1. 实现简单：在 OpenAIProvider 中新增 `score_relevance_batch()` 方法，prompt 结构复用 `score_relevance()`
2. 兼容性好：保留 `score_relevance()` 不变，batch 失败自动 fallback
3. API 调用从 200 次降到 ~40 次（batch_size=5），总延迟降低 60%+
4. 风险可控：JSON 解析失败只影响单个 batch，fallback 到逐篇

## 影响

- FilteringManager.filter_papers() 内部逻辑变化，签名不变
- 新增 LLMProvider 方法 score_relevance_batch()
- 新增配置项 batch_size（默认 5）
- 需测试 batch 模式与逐篇模式的评分一致性

## 后验观察

[待实现后填写]
