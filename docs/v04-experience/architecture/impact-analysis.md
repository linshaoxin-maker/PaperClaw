# v04-experience — 变更影响分析

**Phase:** Phase 3
**Last Updated:** 2026-03-15

---

## 1. 变更清单

| # | 变更 | 文件 | 类型 |
|---|------|------|------|
| C-01 | `to_summary_dict()` 新增 3 字段 | `domain/models/paper.py` | 向后兼容 |
| C-02 | `to_detail_dict()` 新增 8 字段 | `domain/models/paper.py` | 向后兼容 |
| C-03 | `to_compact_dict()` 新增 1 字段 | `domain/models/paper.py` | 向后兼容 |
| C-04 | `_format_paper()` 增加展示字段 | `services/digest_generator.py` | 格式变更 |
| C-05 | 新增 `score_relevance_batch()` | `infra/llm/openai_provider.py` | 新增方法 |
| C-06 | 新增 `score_relevance_batch()` | `infra/llm/anthropic_provider.py` | 新增方法 |
| C-07 | `filter_papers()` 重构为 batch + prefilter + feedback | `services/filtering_manager.py` | 行为变更 |
| C-08 | `paper_download` DOI Content-Type 检查 | `mcp/tools.py` | 行为增强 |
| C-09 | `paper_find_and_download` bug fix + metadata persist | `mcp/tools.py` | Bug fix |
| C-10 | Router Skill 新增 8 个意图映射 | `cli/_skill_content.py` | 内容变更 |
| C-11 | plugin/ 目录 Skill 同步 | `plugin/claude-code/skills/*.md` | 内容变更 |
| C-12 | Deep-dive Skill 信息来源标注 | `cli/_skill_content.py` | 内容变更 |

## 2. 影响矩阵

### C-01~C-03: Paper 序列化变更

| 受影响功能 | 影响程度 | 回归测试 |
|-----------|---------|---------|
| `paper_search` (返回 summary_dict) | 低 — 新增字段 | RT-01: 验证返回值含新字段 |
| `paper_show` (返回 detail_dict) | 低 — 新增字段 | RT-02: 验证返回值含新字段 |
| `paper_batch_show` | 低 | RT-01 覆盖 |
| `paper_compare` (使用 compact_dict) | 低 | RT-03: 验证含 methodology_tags |
| `paper_quick_scan` | 低 | RT-01 覆盖 |
| `paper_auto_triage` | 低 | RT-01 覆盖 |
| `paper_morning_brief` | 低 | RT-03 覆盖 |

### C-04: Digest 格式变更

| 受影响功能 | 影响程度 | 回归测试 |
|-----------|---------|---------|
| `paper_digest` / `paper_morning_brief` 输出 | 中 — 格式变化 | RT-04: 验证 digest markdown 可读性和完整性 |
| WorkspaceManager digest 文件 | 中 — 需验证不破坏解析 | RT-10: workspace digest 文件正常 |

### C-05~C-07: Scoring 变更

| 受影响功能 | 影响程度 | 回归测试 |
|-----------|---------|---------|
| `paper_collect` → filter_papers | 高 — 评分逻辑变化 | RT-05: batch vs serial 评分一致性 |
| `paper_morning_brief` → filter | 高 | RT-05 覆盖 |
| 已有评分结果 | 无影响 — 已持久化的 score 不重新计算 | — |

### C-08~C-09: 下载变更

| 受影响功能 | 影响程度 | 回归测试 |
|-----------|---------|---------|
| `paper_download` | 中 — 增加 fallback | RT-07: 非 arXiv 论文下载 |
| `paper_find_and_download` | 高 — bug fix | RT-08: Paper 创建 + metadata |

### C-10~C-12: Skill 变更

| 受影响功能 | 影响程度 | 回归测试 |
|-----------|---------|---------|
| IDE 意图路由 | 中 | RT-09: 新增意图映射测试 |
| Cursor `paper-agent setup` 输出 | 中 | 验证 _skill_content.py 与 plugin/ 一致 |

## 3. 不受影响的模块

以下模块 **不受 v04-experience 任何变更影响**：
- SQLite schema（不变）
- WorkspaceManager（不变，只消费 digest 输出）
- CitationService（不变）
- SearchEngine（只读引用 _SYNONYM_GROUPS）
- CollectionManager（不变）
- PdfProcessor / ExtractionEngine（不变）
- CredibilityAssessor（不变）
- WatchlistManager（不变）
- ResearchPlanner / ResearchEngine（不变）
