# Paper Agent — 追溯矩阵

**Phase:** Seed (Phase 1) → 持续更新至 Phase 5
**Last Updated:** 2026-03-13
**Status:** 种子版（Story→UC→NFR 映射）

---

## 说明

追溯链：`Story → UC → BDD → NFR → Component → API/MCP Tool → Schema → FEAT → 文件 → 函数 → 测试用例 → 通过状态`

当前版本仅包含 Phase 1 的种子列（Story→UC→NFR），后续阶段逐步补充。

**标记说明**：
- `—` 表示当前阶段尚未补充
- `[待补充]` 表示应有但缺失

---

## 核心追溯矩阵

| Story/场景 | UC-ID | FR-ID | NFR-ID | BDD | Component | MCP Tool / API | Schema | FEAT | 文件 | 测试 | 状态 |
|-----------|-------|-------|--------|-----|-----------|---------------|--------|------|------|------|------|
| S1: 首次初始化 | UC-01 | FR-01 | NFR-04 | — | ConfigManager | `paper-agent init` | config.yaml | — | `cli/app.py`, `app/config_manager.py` | — | ✅ 已实现 |
| S2: 每日 Digest | UC-02 | FR-02,03,05 | NFR-03,06 | — | CollectionManager, FilteringManager, DigestGenerator | `paper_collect`, `paper_digest` | papers, digest | — | `services/collector.py`, `services/digest.py` | — | ✅ 已实现 |
| S3: 问题检索 | UC-03 | FR-07,08 | NFR-01,02 | — | SearchEngine | `paper_search` | papers (FTS5) | — | `services/search.py` | — | ✅ 已实现 |
| S4: Topic Report | UC-04 | FR-09,11 | NFR-07 | — | TopicReportGenerator | — | — | — | — | — | 🔲 未实现 |
| S5: Agent 调用 | UC-05 | FR-12,13 | NFR-02,05 | — | MCP Server | 全部 MCP Tools | — | — | `mcp/server.py`, `mcp/tools.py` | — | ✅ 已实现 |
| S6: 方法相似性 | UC-06 | FR-14 | — | — | MethodologyExtractor | — | methodology_tags | — | — | — | 🔲 未实现 |
| S7: 目标发现 | UC-07 | FR-15 | — | — | ObjectiveExtractor | — | research_objectives | — | — | — | 🔲 未实现 |
| S8: 文献综述 | UC-08 | FR-16 | — | — | SurveyGenerator | — | surveys | — | — | — | 🔲 未实现 |
| — Profile 管理 | — | — | — | — | ProfileManager | `paper_profile`, `paper_profile_update` | config.yaml | — | `services/profile_manager.py` | — | ✅ 已实现 |
| — Source 管理 | — | — | — | — | SourceRegistry | `paper_sources_list`, `paper_sources_enable` | sources.yaml | — | `infra/sources/source_registry.py` | — | ✅ 已实现 |
| — Paper 详情 | — | FR-10 | — | — | — | `paper_show` | papers | — | — | — | ✅ 已实现 |
| — IDE 集成 | — | — | — | — | — | `paper-agent setup` | — | — | `cli/commands/setup.py` | — | ✅ 已实现 |

---

## 待补充列说明

| 列 | 补充阶段 | 说明 |
|----|---------|------|
| BDD | Phase 2 | 每行至少一个 BDD 场景 ID (S-XXX-XX) |
| Component | Phase 3 | 已部分填充，需与 C4 L3 对齐 |
| MCP Tool / API | Phase 3 | 已部分填充，需补充参数契约 |
| Schema | Phase 3 | 需与 SQLite DDL 对齐 |
| FEAT | Phase 4 | 按 FEAT-ID 关联 |
| 文件 | Phase 5 | 实现文件路径 |
| 测试 | Phase 5 | TC-ID + 通过状态 |

---

## 覆盖度检查

| 检查项 | 状态 |
|--------|------|
| 每个 FR 至少映射到一个 UC | ✅ FR-01~16 均有 UC |
| 每个 UC 至少映射到一个场景 | ✅ S1~S8 |
| 每个 Must FR 有实现或计划 | ⚠️ FR-11 (Topic Report) 未实现 |
| NFR 均有测量方法 | ✅ NFR-01~08 |
| 无孤立行（无 UC 的 FR 或无 FR 的 UC） | ✅ |
