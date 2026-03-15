# v04-experience — 错误恢复旅程

**Phase:** Phase 2
**Last Updated:** 2026-03-15

---

## 错误场景与恢复路径

### E-01: Batch scoring LLM 返回格式错误

| 项 | 描述 |
|----|------|
| **触发条件** | LLM 对一个 batch 返回非法 JSON 或缺少部分 paper_index |
| **用户看到** | 无感知（内部自动处理） |
| **系统响应** | 该 batch 中未成功评分的论文逐篇重新评分 |
| **恢复路径** | 逐篇评分作为 fallback → 用户最终拿到完整结果 |
| **日志** | `WARNING: Batch scoring failed for batch N, falling back to per-paper scoring` |
| **回正轨** | ≤ 1 步（自动） |

### E-02: Title 预过滤误杀相关论文

| 项 | 描述 |
|----|------|
| **触发条件** | 相关论文 title 中不含 profile keywords 的任何近义词 |
| **用户看到** | 该论文得到 score=1.0（出现在 digest 末尾或不出现） |
| **系统响应** | 无自动恢复（设计假设 ASM-V4-04） |
| **恢复路径** | 用户可通过 `paper_search` 或 `paper_show` 找到论文，手动查看 |
| **缓解措施** | 预过滤只看 title + abstract[:200]，降低误杀概率；配置允许关闭预过滤 |
| **回正轨** | 1 步（搜索找到该论文） |

### E-03: PDF 解析失败

| 项 | 描述 |
|----|------|
| **触发条件** | `paper_parse(paper_id)` 因 PDF 格式问题抛异常 |
| **用户看到** | "PDF 解析遇到问题，将基于摘要进行分析 [基于摘要]" |
| **系统响应** | Deep-dive Skill 自动降级到 abstract-based 分析 |
| **恢复路径** | 用户获得 [基于摘要] 标注的分析报告 |
| **回正轨** | 0 步（自动降级） |

### E-04: PDF 下载 fallback 全部失败

| 项 | 描述 |
|----|------|
| **触发条件** | 论文无 arXiv ID，S2 pdf_url 失效，DOI 指向付费页面 |
| **用户看到** | `"status": "skipped", "reason": "无免费 PDF"` |
| **系统响应** | 返回明确失败原因，区分"付费文章"/"无链接"/"网络错误" |
| **恢复路径** | 用户自行到出版商网站下载，或搜索 preprint 版本 |
| **回正轨** | 1 步（手动下载） |

### E-05: Feedback 偏好冲突

| 项 | 描述 |
|----|------|
| **触发条件** | 用户对同一 topic 既提交过"推荐太多"又提交过"想多看" |
| **用户看到** | 无直接提示（内部使用最近 N 天的 feedback） |
| **系统响应** | `get_adjusted_topic_weights()` 使用时间加权：最近 30 天的 feedback 权重更高 |
| **恢复路径** | 用户通过 `paper_preferences` 查看当前偏好，如有问题可重新 feedback |
| **回正轨** | 1 步（查看偏好后调整） |

### E-06: paper_extract 提取结果不完整

| 项 | 描述 |
|----|------|
| **触发条件** | LLM 无法从论文中提取某些结构化字段（如 datasets、baselines） |
| **用户看到** | 对比表中对应单元格显示 "—"（非空白） |
| **系统响应** | 提取结果中缺失字段标记为 null，对比表显示占位符 |
| **恢复路径** | 用户可通过 `paper_ask(paper_id, "这篇用了什么数据集？")` 追问 |
| **回正轨** | 1 步（追问） |

### E-07: Watchlist 无更新

| 项 | 描述 |
|----|------|
| **触发条件** | 用户设置的 watchlist 在近期无新论文匹配 |
| **用户看到** | "您关注的领域最近无新论文（上次更新: X 天前）" |
| **系统响应** | 展示最后更新时间，不报错 |
| **恢复路径** | 用户可调整 watchlist 关键词范围或等待新论文发布 |
| **回正轨** | 0 步（信息展示，非错误） |

### E-08: FeedbackManager 不可用

| 项 | 描述 |
|----|------|
| **触发条件** | FeedbackManager 初始化失败或 DB 表不存在 |
| **用户看到** | 无感知（推荐结果正常，只是无偏好调整） |
| **系统响应** | FilteringManager 跳过 feedback 偏移，使用 raw score 排序 |
| **恢复路径** | 自动降级 |
| **日志** | `WARNING: FeedbackManager unavailable, skipping preference adjustment` |
| **回正轨** | 0 步（自动） |
