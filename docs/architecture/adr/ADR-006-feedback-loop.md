# ADR-006: Feedback 闭环集成策略

## 基本信息
- 状态: accepted
- 日期: 2026-03-15
- 关联: FR-V4-05, UX-V4-04

## 背景

FeedbackManager 已实现 `compute_preference_adjustments()` 和 `get_adjusted_topic_weights()` 方法，能从用户反馈中计算 topic 偏好权重（+0.1/-0.1 per feedback）和 relevance_bias（±0.5 per override）。但 FilteringManager 和 DigestGenerator 从未读取这些数据——feedback 只是"记录但无效果"。

## 备选方案

| 方案 | 描述 | 优势 | 劣势 |
|---|---|---|---|
| A. 注入 LLM prompt | 在 scoring prompt 中注入偏好信息 | LLM 可"理解"偏好 | 不可控、不可审计、prompt 膨胀 |
| B. Post-scoring 偏移 | LLM 评分后对 score 做确定性偏移 | 可控、可审计、偏移量可配置 | 偏移是机械的，非语义理解 |
| C. DigestGenerator 排序偏移 | 仅在 digest 排序时偏移 | 最小改动 | 其他消费者（recommend、triage）不受益 |

## 决策

选择 **方案 B: Post-scoring 偏移**。

## 理由

1. 偏移逻辑集中在 FilteringManager，所有消费者统一受益
2. 偏移量有 clamp 限制（±2.0），避免推荐漂移
3. 可审计：`paper_preferences` 工具已能展示当前偏好状态
4. FeedbackManager 的 `get_adjusted_topic_weights()` 已提供了 topic→offset 映射，直接可用

## 集成方式

```
FilteringManager.filter_papers()
  ├── pre_filter() — title 预过滤
  ├── batch_scoring() — LLM 评分
  ├── _apply_feedback_offset() — 读取 FeedbackManager 偏好，应用偏移
  └── sort by effective_score
```

偏移计算：
1. 取论文 topics 与 FeedbackManager topic_adjustments 的交集
2. 平均偏移 = sum(交集 offsets) / len(交集)
3. clamp(偏移, -2.0, +2.0)
4. effective_score = clamp(raw_score + 偏移, 0.0, 10.0)

## 影响

- FilteringManager 新增对 FeedbackManager 的依赖
- AppContext 中 FilteringManager 构造需传入 FeedbackManager 引用
- 无 feedback 数据时行为不变（偏移量为 0）

## 后验观察

[待实现后填写]
