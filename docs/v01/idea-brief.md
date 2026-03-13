# Paper Agent — Idea Brief

**Phase:** Phase 0 (想法澄清)
**Status:** Initialized from existing project
**Last Updated:** 2026-03-13

---

## 1. 愿景陈述

> Paper Agent 为 AI 研究员提供一个 **IDE 内嵌的论文智能助手**，通过 CLI + MCP Server 架构，让研究员在 Claude Code / Cursor 中以对话方式完成论文发现、筛选、分析、对比和综述的全链路工作，将日均论文 intake 时间从 30+ 分钟降至 5 分钟以内。

## 2. 范围边界表

| 类别 | 内容 |
|------|------|
| **In Scope** | arXiv 论文收集 + LLM 语义筛选 + 每日 digest + 本地全文检索 + 单篇分析 + Profile/Sources 管理 + IDE 集成 (Cursor + Claude Code) + MCP Server |
| **Out of Scope** | 替代 Zotero/Mendeley (reference manager) · 替代 Obsidian/Notion (笔记系统) · PDF 全文深度解析 · 社交协作 · 引文网络深度分析 · 移动端 · Web UI |
| **Future (v02+)** | 多篇对比/综述 · 联网搜索 (arXiv API/Semantic Scholar) · PDF 下载 + 全文分析 · BibTeX 导出 · MCP Elicitation checkbox · 作者追踪 · 团队共享 |

## 3. 干系人地图

| 角色 | 关注点 | 参与阶段 | 沟通频率 |
|------|--------|---------|---------|
| Individual AI Researcher (主要) | 高信噪比的论文推荐、快速 intake | 需求→验收 | 每日使用 |
| Research Engineer | 实现/复现时快速取回论文上下文 | 需求→验收 | 按需使用 |
| PhD Student / Early Researcher | 快速建立 topic understanding | 需求→验收 | 每日使用 |
| Automation Agent (Cursor/Claude Code) | 稳定 MCP/JSON 接口 | 设计→集成测试 | 实时调用 |
| 开发者 (self) | 架构可扩展性、代码质量 | 全程 | 持续 |

## 4. 开放问题清单

| # | 问题 | 影响 | 状态 |
|---|------|------|------|
| OQ-001 | Topic report 默认是否依赖在线 LLM | 离线能力与依赖约束 | 待确认 |
| OQ-002 | 本地库结果不足时是否显式提示扩展来源 | 查询失败策略 | 待确认 |
| OQ-003 | Topic report 是否支持多版本管理 | artifact 生命周期 | 待确认 |
| OQ-004 | 综述是否支持增量更新 | survey artifact 生命周期 | 待确认 |
| OQ-005 | automation contract 采用 REST-like 还是 Protobuf/gRPC | MCP 已实际选用 stdio JSON-RPC | 已解决 (MCP) |
| OQ-006 | 配置是否采用 YAML + DB profile split | 架构决策 | 待确认 |
| OQ-007 | v02 MCP Elicitation checkbox 对客户端的兼容性 | 多篇选择 UI 实现 | 待确认 |

## 5. 项目类型判定

**项目类型：CLI Tool + MCP Server (SDK/Library 侧重)**

Phase 3 交付件侧重参考：

| 交付件 | 侧重 |
|--------|------|
| C4 Container 图 | ★★ |
| ER 图 + Schema | ★★★ |
| 时序图 | ★★ |
| 状态机 | ★ |
| API 契约 (OpenAPI) | ★ (MCP 工具定义替代) |
| 类型契约 (TS/Proto) | ★ |
| 函数契约 (Pre/Post) | ★★★ |
| 算法规格 | ★★ (LLM prompt 策略) |
| 模块依赖图 | ★★★ |
| ADR | ★★★ |

## 6. 现有文档映射

本项目在方法论引入前已有大量文档和实现代码。下表映射现有文档到 6 阶段框架：

### Phase 0 — 想法澄清 (Idea)

| 交付件 | 现有文档 | 覆盖度 | 备注 |
|--------|---------|--------|------|
| 愿景陈述 | `docs/paper-agent-overview.md` §1 | ⚠️ 部分 | 有产品定位但非正式愿景格式 |
| C4 Context 图 | `docs/v01/design.md` §1 (C4 L2) | ✅ 有 | 已有 Mermaid C4 图 |
| 用户旅程图 | `docs/v01/user-journey.md` | ✅ 完整 | 含情感曲线、错误恢复 |
| 用户故事地图 | — | ❌ 缺失 | 无 Activity→Task→Story 结构 |
| 范围边界表 | `docs/v01/requirement.md` §1.8 | ✅ 有 | In/Out 划分明确 |
| 领域术语表 | — | ❌ 缺失 | — |
| 开放问题清单 | `docs/v01/design.md` Open Issues | ⚠️ 分散 | 散落在设计文档中，已整理至本文档 |
| 干系人地图 | `docs/v01/requirement.md` §1.5 | ⚠️ 部分 | 有目标用户但无参与阶段/沟通频率 |

### Phase 1 — 需求定义 (Requirement)

| 交付件 | 现有文档 | 覆盖度 | 备注 |
|--------|---------|--------|------|
| Requirement Doc | `docs/v01/requirement.md` | ✅ 完整 | FR-01~16, BR-01~06 |
| 用例规约 | `docs/v01/requirement.md` §2 | ✅ 完整 | UC-01~08，含主/扩展流程 |
| NFR 规格 | `docs/v01/requirement.md` §3 | ✅ 有 | NFR-01~08 含量化指标 |
| 体验指标 (UX) | — | ❌ 缺失 | 无 UX-ID 量化体验指标 |
| 假设登记表 | `docs/v01/requirement.md` §4 | ✅ 完整 | ASM 表格完整 |
| 追溯矩阵种子 | — | ❌ 缺失 | 无 Story→UC→NFR 矩阵 |

### Phase 2 — 功能规格 (Spec)

| 交付件 | 现有文档 | 覆盖度 | 备注 |
|--------|---------|--------|------|
| Functional Spec | `docs/v01/spec.md` | ✅ 完整 | 详细的功能行为定义 |
| BDD 场景 | — | ❌ 缺失 | 无 Gherkin .feature 文件 |
| 决策表 | — | ❌ 缺失 | 复杂规则未穷举 |
| 错误恢复旅程 | `docs/v01/user-journey.md` | ✅ 有 | 含错误恢复策略 |

### Phase 3 — 技术设计 (Design)

| 交付件 | 现有文档 | 覆盖度 | 备注 |
|--------|---------|--------|------|
| C4 L2 Container 图 | `docs/v01/design.md` §1 | ✅ 有 | Mermaid |
| C4 L3 Component 图 | `docs/v01/design.md` §2 | ✅ 有 | Mermaid |
| 逻辑视图 (ER/Schema) | `docs/v01/design.md` | ✅ 有 | SQLite Schema 定义 |
| 过程视图 (时序/状态机) | `docs/v01/design.md` | ⚠️ 部分 | 有数据流但无正式时序图 |
| 开发视图 (目录/依赖) | `docs/v01/developer-journey.md` | ✅ 有 | 目录结构 + 模块说明 |
| API 契约 | — | ⚠️ 隐式 | MCP tool 签名在代码中，无独立契约文件 |
| 函数契约 | — | ❌ 缺失 | 无 Pre/Post 条件定义 |
| 设计模式清单 | — | ❌ 缺失 | 实际用了适配器/注册表等模式但未记录 |
| ADR | — | ❌ 缺失 | 关键决策散落在文档中未形式化 |
| 变更影响分析 | — | ❌ 缺失 | — |
| 接口兼容性声明 | — | ❌ 缺失 | — |
| 可观测性设计 | — | ❌ 缺失 | — |

### Phase 4 — 特性拆解 (Feature)

| 交付件 | 现有文档 | 覆盖度 | 备注 |
|--------|---------|--------|------|
| 特性清单 | `docs/v01/feature.md` | ⚠️ 格式不符 | 有特性描述但无 FEAT-ID/四可检验/AC/DoD |
| 用户旅程切片 | — | ❌ 缺失 | — |
| 演示脚本 | `README.md` End-to-End Demo | ⚠️ 部分 | 有演示流程但非按 Feature 组织 |
| 依赖 DAG | — | ❌ 缺失 | — |
| 迭代计划 | `docs/v01/mvp.md` §8 | ⚠️ 部分 | 有 Phase 1-7 时间线但非 Feature 粒度 |
| 变更影响矩阵 | — | ❌ 缺失 | — |

### Phase 5 — MVP 交付 (Code + 验证)

| 交付件 | 现有文档 | 覆盖度 | 备注 |
|--------|---------|--------|------|
| MVP Scope Doc | `docs/v01/mvp.md` | ✅ 完整 | 含验收标准 |
| 代码实现 | `paper_agent/` | ✅ 已实现 | CLI + MCP + 核心服务 |
| 测试 | — | ❓ 待查 | 需检查测试覆盖 |
| Feature 验证报告 | — | ❌ 缺失 | — |
| 活文档更新 | — | ❌ 缺失 | — |
| 知识沉淀 | — | ❌ 缺失 | — |
| 追溯矩阵终版 | — | ❌ 缺失 | — |

### 版本扩展文档

| 文档 | 路径 | 覆盖 |
|------|------|------|
| v01_source 需求 | `docs/v01_source/requirement.md` | ✅ 多源扩展需求 |
| v01_source 规格 | `docs/v01_source/spec.md` | ✅ Source/Profile 行为 |
| v01_source 设计 | `docs/v01_source/design.md` | ✅ 组件/适配器/注册表 |
| v01_source 特性 | `docs/v01_source/feature.md` | ✅ 特性视图 |
| v01_source MVP | `docs/v01_source/mvp.md` | ✅ 首发范围 |
| 产品总览 | `docs/paper-agent-overview.md` | ✅ 全链路工作流 + 交互设计 |

## 7. 差距分析与优先行动

### 优先补全 (P0)

| # | 缺失制品 | 阶段 | 理由 |
|---|---------|------|------|
| 1 | **领域术语表** | P0 | 统一用语是后续所有文档一致性的基础 |
| 2 | **追溯矩阵种子** | P1 | 当前无法验证需求→用例→规格→实现的完整覆盖 |
| 3 | **ADR (关键决策记录)** | P3 | 多个 `[待决策]` 项实际已在实现中做了选择但未记录 |

### 建议补全 (P1)

| # | 缺失制品 | 阶段 | 理由 |
|---|---------|------|------|
| 4 | 体验指标 (UX) | P1 | 当前无用户体验量化基线 |
| 5 | BDD 场景 | P2 | 无可执行验收标准 |
| 6 | 函数契约 | P3 | 核心函数无形式化 Pre/Post |
| 7 | 设计模式清单 | P3 | 实际已用但未记录 |

### 可延后 (P2)

| # | 缺失制品 | 阶段 | 理由 |
|---|---------|------|------|
| 8 | 用户故事地图 | P0 | 现有用户旅程已足够清晰 |
| 9 | 决策表 | P2 | 当前规则不多(<3 条件) |
| 10 | 变更影响分析 | P3/P4 | 项目初期可在 v02 引入 |
| 11 | Feature 验证报告 | P5 | 回溯补充成本高，从下一个 Feature 开始执行 |

## 8. 初始化完成状态

本 Idea Brief 标志着方法论已引入项目。后续工作：

- [x] 目录结构已创建 (`docs/` 按方法论结构)
- [x] 现有文档映射完成
- [x] 差距分析完成
- [x] 开放问题统一整理
- [ ] 领域术语表 → `docs/glossary.md`
- [ ] 追溯矩阵种子 → `docs/traceability-matrix.md`
- [ ] 首批 ADR → `docs/architecture/adr/`
