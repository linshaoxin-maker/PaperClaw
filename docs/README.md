# Paper Agent Documentation

## 文档结构

本项目采用 **AI 辅助开发 6 阶段方法论**，文档按以下结构组织：

```
docs/
├── idea-brief.md                    # Phase 0: 想法澄清 + 现有文档映射 + 差距分析
├── glossary.md                      # Phase 0: 领域术语表
├── paper-agent-overview.md          # 产品总览：全链路工作流 + 交互设计 + 路线图
├── traceability-matrix.md           # 全程追溯矩阵（Phase 1 种子 → Phase 5 终版）
│
├── v01/                             # v01 版本文档（方法论引入前已有）
│   ├── requirement.md               # Phase 1: 需求定义 (FR/UC/NFR/假设)
│   ├── spec.md                      # Phase 2: 功能规格
│   ├── design.md                    # Phase 3: 技术设计 (C4/Schema/组件)
│   ├── feature.md                   # Phase 4: 特性视图
│   ├── mvp.md                       # Phase 5: MVP 范围
│   ├── user-journey.md              # Phase 0/1: 用户旅程 + 错误恢复
│   └── developer-journey.md         # Phase 3: 开发者旅程
│
├── v01_source/                      # v01 扩展版本：多源收集 + Profile
│   ├── requirement.md
│   ├── spec.md
│   ├── design.md
│   ├── feature.md
│   └── mvp.md
│
├── architecture/                    # Phase 3: 架构制品
│   ├── adr/                         # 架构决策记录
│   │   ├── ADR-001-mcp-as-ide-integration.md
│   │   ├── ADR-002-sqlite-local-first.md
│   │   └── ADR-003-interaction-layer-division.md
│   ├── c4/                          # C4 图 (现存于 v01/design.md)
│   ├── views/                       # 4+1 视图
│   ├── contracts/                   # API/函数契约
│   └── observability/               # 可观测性设计
│
├── features/                        # Phase 4: 特性规格 (按 FEAT-ID 组织)
│
├── mvp/                             # Phase 5: MVP Scope
│
├── journeys/                        # 用户/开发者/错误恢复旅程
│
├── requirements/                    # Phase 1-2 制品
│   ├── use-cases/
│   ├── bdd/                         # BDD 场景 (.feature)
│   └── decision-tables/
│
├── spec/                            # Phase 2: Functional Spec
│
└── project-knowledge/               # 项目知识沉淀
    ├── decisions/                   # 重要决策归档
    ├── features/                    # 每个 Feature 的经验沉淀
    ├── incidents/                   # 事故记录
    ├── patterns/                    # 可复用模式库
    └── anti-patterns/               # 反模式记录
```

## 阅读指南

### 了解产品
1. `idea-brief.md` — 项目全貌、愿景、范围
2. `paper-agent-overview.md` — 产品定位 + 10 环节交互设计 + 路线图

### 了解需求与设计
3. `v01/requirement.md` — 需求定义
4. `v01/spec.md` — 功能规格
5. `v01/design.md` — 技术设计
6. `architecture/adr/` — 关键架构决策

### 了解实现与验证
7. `v01/feature.md` — 特性视图
8. `v01/mvp.md` — MVP 范围
9. `traceability-matrix.md` — 需求追溯

### 版本演进
- `v01/` → 基础版本
- `v01_source/` → 多源扩展
- `paper-agent-overview.md` §4, §7 → v02 规划

## 方法论阶段映射

| 阶段 | 主要文档 | 状态 |
|------|---------|------|
| Phase 0 想法澄清 | `idea-brief.md`, `glossary.md`, `v01/user-journey.md` | ✅ 完成 |
| Phase 1 需求定义 | `v01/requirement.md`, `traceability-matrix.md` | ✅ 完成 |
| Phase 2 功能规格 | `v01/spec.md` | ✅ 完成 (BDD 待补) |
| Phase 3 技术设计 | `v01/design.md`, `architecture/adr/` | ✅ 完成 (契约待补) |
| Phase 4 特性拆解 | `v01/feature.md` | ⚠️ 格式待对齐 |
| Phase 5 MVP 交付 | `v01/mvp.md`, `paper_agent/` 代码 | ✅ 已实现 |
