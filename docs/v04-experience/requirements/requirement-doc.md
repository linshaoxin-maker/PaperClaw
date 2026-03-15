# Paper Agent v04-experience — Requirement Doc

**Phase:** Phase 1 (需求定义)
**Last Updated:** 2026-03-15
**Baseline:** `../../v03/feature-list.md`

---

## 1. 背景

v03 完成了"能力下沉"（50+ MCP 工具 + Skill 层升级），但研究者实际使用中仍有以下体验摩擦：

1. **信息密度不足**：Digest 只展示 title + score + authors + abstract（6 字段），缺少 topics、methodology_tags、发布日期、来源等关键判断信息
2. **序列化缺口**：Paper model 有 7 个字段（reading_status, canonical_key, source_paper_id, metadata, created_at, updated_at, reading_status_at）未出现在 `to_summary_dict()` 或 `to_detail_dict()` 中
3. **Scoring 性能**：FilteringManager 虽已并行（ThreadPoolExecutor, max_workers=8），但每个 worker 仍做 1 篇/LLM 调用，200 篇需 25 次 API 调用（受限于 rate limit）
4. **反馈断路**：`paper_feedback` / `paper_preferences` 记录了用户偏好但 FilteringManager 和 DigestGenerator 从未读取
5. **PDF 下载盲区**：`paper_download` 的 DOI fallback 指向 landing page 而非 PDF；`paper_find_and_download` 有 bug（`source=` 应为 `source_name=`）且不持久化 `pdf_url`
6. **16 个工具无引用**：paper_preferences, paper_watch_check, paper_tables, paper_query 等工具未被任何 Skill/Command 引用

## 2. 功能需求 (FR)

### FR-V4-01: Paper 序列化补全

**描述**：`to_summary_dict()` 和 `to_detail_dict()` 新增关键字段，让 MCP 消费者获得完整的论文信息。

**需求条目**：

| 子项 | 需求 | 验证标准 |
|------|------|---------|
| FR-V4-01a | `to_summary_dict()` 新增 `reading_status` 字段 | 返回值中包含 reading_status（null 当未设置） |
| FR-V4-01b | `to_summary_dict()` 新增 `canonical_key` 字段 | 返回值中包含 canonical_key |
| FR-V4-01c | `to_summary_dict()` 新增 `published_at` 已有，新增 `source_paper_id` | 返回值中包含 source_paper_id |
| FR-V4-01d | `to_detail_dict()` 新增 `reading_status`, `canonical_key`, `source_paper_id`, `created_at` | 返回值含这 4 个字段 |
| FR-V4-01e | `to_detail_dict()` 新增 `metadata` 子集（`pdf_url`, `doi`, `citation_count`, `venue`） | 返回值含 metadata 中的关键信息 |
| FR-V4-01f | `to_compact_dict()` 新增 `methodology_tags` | 返回值含 methodology_tags |

### FR-V4-02: Digest 信息密度提升

**描述**：`DigestGenerator._format_paper()` 增加结构化字段，让研究者在 digest 中就能做出"值不值得读"的判断。

**需求条目**：

| 子项 | 需求 | 验证标准 |
|------|------|---------|
| FR-V4-02a | Digest 每篇论文展示 `topics`（标签列表） | digest markdown 中可见 topics 标签 |
| FR-V4-02b | Digest 每篇论文展示 `methodology_tags` | digest markdown 中可见方法标签 |
| FR-V4-02c | Digest 每篇论文展示 `published_at`（发布日期） | digest markdown 中可见日期 |
| FR-V4-02d | Digest 每篇论文展示 `source_name`（来源） | digest markdown 中可见来源 |
| FR-V4-02e | Digest 每篇论文展示 `canonical_key`（arXiv ID / S2 ID） | digest markdown 中可见标识符 |
| FR-V4-02f | 新增字段不得破坏已有 digest 格式的可读性 | 格式审查通过，信息紧凑不杂乱 |

### FR-V4-03: LLM Batch Scoring

**描述**：FilteringManager 支持在一次 LLM 调用中评估多篇论文，减少 API 调用次数和总延迟。

**需求条目**：

| 子项 | 需求 | 验证标准 |
|------|------|---------|
| FR-V4-03a | 新增 batch scoring 能力：一次 LLM 调用评估 N 篇论文（N 可配置，默认 5） | `_call_llm_batch(papers, interests)` 方法存在且可用 |
| FR-V4-03b | batch 结果与逐篇结果对每篇论文返回相同字段（score, band, reason, topics） | 输出格式一致 |
| FR-V4-03c | batch 评分失败时自动 fallback 到逐篇评分 | 失败后逐篇 rescore 成功 |
| FR-V4-03d | 可配置 batch size（默认 5，最大 10） | 配置项生效 |

### FR-V4-04: Title 预过滤

**描述**：在 LLM scoring 前用 profile keywords/topics 快速排除明显不相关论文，减少 LLM 调用。

**需求条目**：

| 子项 | 需求 | 验证标准 |
|------|------|---------|
| FR-V4-04a | 对 title 和 abstract 前 200 字符做关键词匹配 | 匹配逻辑正确 |
| FR-V4-04b | 匹配源为 profile 的 topics + keywords + 已有 topic 的同义词 | 使用正确的匹配源 |
| FR-V4-04c | 不匹配的论文直接标记为 `score=1.0, band="low"` 并跳过 LLM | 跳过行为正确 |
| FR-V4-04d | 预过滤可通过配置关闭 | 配置项生效 |
| FR-V4-04e | 预过滤结果在日志中标注 `[pre-filtered]` | 日志可见 |

### FR-V4-05: Feedback 闭环

**描述**：用户通过 `paper_feedback` 提交的偏好反馈实际影响后续的推荐和评分。

**需求条目**：

| 子项 | 需求 | 验证标准 |
|------|------|---------|
| FR-V4-05a | FilteringManager 在 scoring 前读取 `FeedbackManager.get_adjusted_topic_weights()` | 调用存在 |
| FR-V4-05b | topic 权重调整应用为 score 偏移（±加分/减分） | 偏移逻辑正确 |
| FR-V4-05c | 偏移幅度有上限（±2.0 分）避免过度漂移 | 上限约束生效 |
| FR-V4-05d | DigestGenerator 在排序时考虑 feedback 偏移后的有效 score | 排序正确反映偏好 |
| FR-V4-05e | `paper_preferences` 工具在 Skill 中可达 | router skill 中有 "我的偏好" 意图映射 |

### FR-V4-06: PDF 下载增强

**描述**：提升非 arXiv 论文的 PDF 下载成功率。

**需求条目**：

| 子项 | 需求 | 验证标准 |
|------|------|---------|
| FR-V4-06a | `paper_download` 的 DOI fallback 尝试 `https://doi.org/{doi}` 后检查 Content-Type 是否为 PDF | 非 PDF 响应不保存 |
| FR-V4-06b | `paper_find_and_download` 修复 `source=` → `source_name=` 参数名 bug | 创建 Paper 不再报错 |
| FR-V4-06c | `paper_find_and_download` 将 S2 openAccessPdf URL 持久化到 Paper.metadata | 后续 paper_download 可用 |
| FR-V4-06d | 下载失败时返回明确的失败原因（"无免费全文" vs "网络错误" vs "链接失效"） | 失败消息区分 |

### FR-V4-07: 未引用工具覆盖

**描述**：将 16 个未被任何 Skill/Command 引用的工具接入适当的 Skill 或 Router。

**需求条目**：

| 子项 | 需求 | 验证标准 |
|------|------|---------|
| FR-V4-07a | `paper_preferences` 加入 Router Skill 意图映射 | "我的偏好" / "我喜欢什么" → paper_preferences |
| FR-V4-07b | `paper_watch_check` 加入 Router Skill | "最近有新论文吗" → paper_watch_check |
| FR-V4-07c | `paper_watch_list` 加入 Router Skill | "我关注了什么" → paper_watch_list |
| FR-V4-07d | `paper_tables` 加入 Deep-dive Skill | 全文分析时展示提取的表格 |
| FR-V4-07e | `paper_query` 加入 Router Skill | "哪些论文用了 GNN" → paper_query |
| FR-V4-07f | `paper_reading_stats` 加入 Router Skill | "我的阅读进度" → paper_reading_stats |
| FR-V4-07g | `paper_note_show` 加入 Router Skill | "看看我对这篇的笔记" → paper_note_show |
| FR-V4-07h | `paper_workspace_status` 加入 Router Skill | "工作区概览" → paper_workspace_status |
| FR-V4-07i | `_skill_content.py` 与 `plugin/` 目录同步更新 | 内容一致 |

### FR-V4-08: Skill 条件分支优化

**描述**：在已有 Skill 中添加更智能的条件分支，减少不必要的工具调用。

**需求条目**：

| 子项 | 需求 | 验证标准 |
|------|------|---------|
| FR-V4-08a | Compare Skill：对比前检测论文是否有 PaperProfile，无则自动调用 `paper_extract` | Skill 文本中含条件分支描述 |
| FR-V4-08b | Survey Skill：生成综述前调用 `paper_trend_data` 和 `paper_field_stats` 预填充数据 | Skill 文本中含预填充步骤 |
| FR-V4-08c | Deep-dive Skill：分析结果标注信息来源 `[基于全文]` 或 `[基于摘要]` | Skill 文本中有标注要求 |

---

## 3. 用例规约

### UC-V4-01: 查看增强 Digest

**前置条件**：论文已收集并评分

**主流程**：
1. 研究者请求每日推荐
2. 系统调用 `paper_morning_brief`
3. 系统生成增强版 digest markdown
4. 每篇论文展示 title + score + authors + topics + methodology_tags + published_at + source_name + canonical_key + abstract + reason

**扩展流程**：
- 4a. 论文无 methodology_tags → 显示空（不报错）
- 4b. 论文无 canonical_key → 使用 paper.id 作为标识

**后置条件**：研究者可基于 digest 信息做出"是否深入"的判断

---

### UC-V4-02: Batch 评分

**前置条件**：新论文已收集，profile 已配置

**主流程**：
1. 系统将论文按 batch_size 分组
2. 对每组调用 `_call_llm_batch(batch, interests)`
3. LLM 返回每篇论文的 score/band/reason/topics
4. 系统应用偏好偏移（如有 feedback 数据）
5. 系统持久化评分结果

**扩展流程**：
- 2a. batch 调用失败 → 该 batch 逐篇重试
- 4a. 无 feedback 数据 → 跳过偏移步骤

**后置条件**：所有论文已评分，耗时 ≤ 逐篇模式的 40%

---

### UC-V4-03: Title 预过滤

**前置条件**：新论文已收集，profile keywords/topics 可用

**主流程**：
1. 系统遍历每篇论文的 title + abstract 前 200 字符
2. 对每篇与 profile topics/keywords 做关键词匹配（含同义词）
3. 匹配命中 → 进入 LLM scoring 队列
4. 未命中 → 标记为 score=1.0, band="low", reason="title pre-filtered"

**扩展流程**：
- 2a. profile 无 keywords/topics → 跳过预过滤，全部进入 LLM scoring
- 2b. 预过滤配置关闭 → 跳过

**后置条件**：进入 LLM 的论文数减少 30%+ 

---

### UC-V4-04: Feedback 影响推荐

**前置条件**：用户已通过 `paper_feedback` 提交过偏好反馈

**主流程**：
1. 用户请求 digest/推荐
2. FilteringManager 读取 FeedbackManager 的 topic 权重调整
3. 对每篇论文的 LLM score 应用 topic 偏移
4. 按调整后的 effective_score 排序
5. DigestGenerator 使用 effective_score 生成 digest

**扩展流程**：
- 2a. 无 feedback 数据 → 使用原始 score

**后置条件**：用户感知到推荐排序与自己的反馈一致

---

### UC-V4-05: 增强 PDF 下载

**前置条件**：用户请求下载论文 PDF

**主流程**：
1. 检查 arXiv ID → 构建 arXiv PDF URL
2. arXiv 下载成功 → 返回
3. 检查 metadata.pdf_url（S2 openAccessPdf）→ 下载
4. 检查 metadata.doi → 尝试 DOI redirect，检查 Content-Type
5. Content-Type 为 PDF → 保存
6. 所有 fallback 失败 → 返回 "无免费全文"

**扩展流程**：
- 4a. DOI redirect 返回 HTML → 不保存，报告 "付费文章"
- 3a. S2 URL 返回 404 → 继续 DOI fallback

**后置条件**：PDF 文件已保存或返回明确失败原因

---

### UC-V4-06: 查看未引用工具

**前置条件**：用户表达相关意图

**主流程**：
1. 用户说"我的偏好"/"我喜欢什么方向"
2. Router Skill 识别意图，路由到 `paper_preferences`
3. 系统返回偏好总结

**类似流程**：
- "我的阅读进度" → `paper_reading_stats`
- "工作区概览" → `paper_workspace_status`
- "我关注了什么" → `paper_watch_list`
- "看看我对这篇的笔记" → `paper_note_show`

---

## 4. 非功能需求 (NFR)

| NFR-ID | 类别 | 需求 | 量化指标 | 测量方法 |
|--------|------|------|---------|---------|
| NFR-V4-01 | 性能 | Batch scoring 200 篇论文总耗时 ≤ 逐篇模式的 40% | 耗时对比 | 基准测试 |
| NFR-V4-02 | 性能 | Title 预过滤 200 篇论文 ≤ 500ms（纯 Python，无 LLM） | 执行时间 | 计时 |
| NFR-V4-03 | 兼容性 | `to_summary_dict()` 新增字段不破坏已有 MCP 消费者 | 新增字段为 optional | 类型检查 |
| NFR-V4-04 | 兼容性 | Digest markdown 格式变化不破坏 Workspace 文件解析 | WorkspaceManager 正常工作 | 集成测试 |
| NFR-V4-05 | 可靠性 | Batch scoring 失败 fallback 到逐篇模式成功率 100% | 无死锁/无挂起 | 异常测试 |
| NFR-V4-06 | 可靠性 | PDF 下载 fallback 链中任一环节超时（30s）自动跳到下一环节 | 无无限等待 | 超时测试 |
| NFR-V4-07 | 可维护性 | `_skill_content.py` 与 `plugin/` 目录内容一致 | diff 检查无差异 | 脚本校验 |

---

## 5. 体验指标 (UX)

| UX-ID | 类别 | 指标 | 目标值 | 测量方法 |
|-------|------|------|--------|---------|
| UX-V4-01 | 效率 | 从 digest 中判断"是否值得深入"的所需信息字段数 | ≥ 6 字段（当前 3） | Digest 格式审查 |
| UX-V4-02 | 速度 | 200 篇论文 scoring 总耗时 | ≤ 2 分钟 | 计时 |
| UX-V4-03 | 可达性 | 用户自然语言意图能路由到的 MCP 工具比例 | ≥ 85%（当前 ~70%） | 意图覆盖率审计 |
| UX-V4-04 | 信任感 | Feedback 后下次推荐排序可见变化 | 用户反馈后 1 次 digest 内可见 | 用户测试 |
| UX-V4-05 | 完成率 | PDF 下载成功率 | ≥ 75%（当前 ~50%） | 统计 |

---

## 6. 假设登记

| ASM-ID | 假设 | 影响 | 确认计划 |
|--------|------|------|---------|
| ASM-V4-01 | LLM 能在单次调用中稳定评估 5 篇论文并返回结构化 JSON | Batch scoring 可行性 | 用 3 篇/批试跑验证 |
| ASM-V4-02 | S2 openAccessPdf URL 有效率 ≥ 50% | 下载成功率提升幅度 | 对 100 篇 S2 论文统计 |
| ASM-V4-03 | Feedback 权重偏移 ±1.0 足以影响排序且不过度漂移 | 推荐稳定性 | 前后 digest 对比 |
| ASM-V4-04 | Title 预过滤不会误杀相关论文（假阴率 < 5%） | 评分覆盖完整性 | 对 200 篇人工标注对比 |
| ASM-V4-05 | Skill 条件分支中的自然语言逻辑 AI IDE 能准确执行 | 条件分支可靠性 | 端到端测试 |

---

## 7. 追溯矩阵种子

见 `docs/v04-experience/traceability-matrix.md`（下方更新）。
