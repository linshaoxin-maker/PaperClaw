# v04-experience: 能力上浮 + 体验打磨

## 基本信息
- 状态: shipped
- 版本: v04-experience
- 日期: 2026-03-15

## 背景
v03 完成了"能力下沉"（50+ MCP 工具），但 Skill 层已同步更新至 v03-v06 工具。v04-experience 的实际焦点转为：序列化缺口补全、信息密度提升、batch scoring 性能优化、反馈闭环建立、PDF 下载增强、未引用工具覆盖。

## 决策记录

### ADR-005: Batch Scoring 策略
选择 batch prompt（5 篇/次）而非两阶段评分。理由：实现简单、兼容现有 provider 接口、fallback 逻辑清晰。API 调用从 200 次降至 ~40 次。

### ADR-006: Feedback 闭环策略
选择 post-scoring 偏移而非 prompt 注入。理由：可控、可审计、偏移量可配置（clamp ±2.0），所有消费者统一受益。

## 经验教训

### 1. Skill 层的同步状态被审计误判
初始审计认为 Skill 停留在 v02 水平（仅引用 15 个基础工具），但实际 `_skill_content.py` 和 `plugin/` 目录中的 Skills 已在 v03 阶段大幅更新，引用了 v03-v06 的大量工具。教训：**审计前先完整读取实际代码，不要基于版本号推断内容**。

### 2. 序列化方法中遗漏字段的累积效应
`to_summary_dict()` 和 `to_detail_dict()` 在 v01 创建后未随 Paper model 的字段扩展同步更新（如 reading_status、canonical_key 等 7 个字段缺失）。教训：**每次给 model 加字段时，应检查所有序列化方法是否需要同步**。

### 3. Feedback 数据"存了不用"
FeedbackManager 的 `get_adjusted_topic_weights()` 早在 v05 就实现了，但 FilteringManager 从未调用。教训：**功能实现后必须与消费者连通，否则用户感知不到价值**。

### 4. paper_find_and_download 参数名 Bug
使用 `source=` 而非 `source_name=` 创建 Paper 对象，且未持久化 metadata。教训：**Paper dataclass 的字段名在不同上下文中不统一是 bug 来源，应在 review 时重点检查**。

## 可复用模式

### Batch LLM 调用模式
在 LLMProvider 基类中实现 `score_relevance_batch()`，使用 JSON 数组作为输入/输出格式，单次 API 调用评估多个输入。失败时 fallback 到逐项调用。此模式可扩展到其他 LLM 操作（如 batch extract、batch classify）。

### 配置化降级模式
FilteringManager 的 pre_filter_enabled 和 batch_size 可通过构造函数配置。任何可能影响结果质量的优化都应提供关闭/调参的能力。

## 应避免的做法

### 不要在 MCP 工具函数中直接构建 domain 对象
`paper_find_and_download` 中直接 `Paper(...)` 构建对象，容易遗漏字段或用错参数名。应统一通过 adapter/factory 构建。

## 验证结果
- 8 个 FEAT 全部通过四可检验
- Paper 序列化、Digest 格式、FilteringManager、PDF 下载、Router Skill、Deep-dive Skill 全部按契约实现
- 需实际 LLM 调用验证 batch scoring 一致性（ASM-V4-01）

## 相关记录
- ADR-005: docs/architecture/adr/ADR-005-batch-scoring.md
- ADR-006: docs/architecture/adr/ADR-006-feedback-loop.md
