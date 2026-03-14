# Paper Agent Documentation

## 文档结构

本项目采用 **AI 辅助开发 6 阶段方法论**，文档按以下标准结构组织：

```
docs/
├── README.md                                ← 你在这里
├── glossary.md                              ← 全局：领域术语表
├── paper-agent-overview.md                  ← 全局：产品总览 (工作流 + 路线图)
│
├── project-knowledge/                       ← 全局：知识沉淀
│   ├── decisions/                           ← 重要决策归档
│   ├── features/                            ← Feature 经验沉淀
│   ├── incidents/                           ← 事故记录
│   ├── patterns/                            ← 可复用模式库
│   └── anti-patterns/                       ← 反模式记录
│
├── architecture/                            ← 全局：架构决策
│   └── adr/
│       ├── ADR-001-mcp-as-ide-integration.md
│       ├── ADR-002-sqlite-local-first.md
│       ├── ADR-003-interaction-layer-division.md
│       └── ADR-004-workspace-layer.md
│
├── v02/                                     ← 版本级文档 (Workspace Layer)
│   ├── requirements/requirement-doc.md
│   ├── spec/functional-spec.md
│   ├── architecture/design-doc.md
│   ├── features/feature-list.md
│   └── journeys/user-journey.md
│
└── v01/                                     ← 版本级文档 (v01 + v01_source 合并)
    ├── README.md                            ← 版本概览
    ├── README-source.md                     ← 多源扩展概览 (原 v01_source)
    ├── idea-brief.md                        ← Phase 0: 想法澄清 + 差距分析
    ├── traceability-matrix.md               ← 追溯矩阵
    │
    ├── journeys/                            ← 用户/开发者旅程
    │   ├── user-journey.md                  ← 用户旅程 + 错误恢复
    │   ├── developer-journey.md             ← 开发者旅程
    │   └── error-recovery.md                ← 错误恢复 (待拆分)
    │
    ├── requirements/                        ← Phase 1: 需求定义
    │   ├── requirement-doc.md               ← 基础需求 (FR/UC/NFR/假设)
    │   ├── requirement-doc-source.md        ← 多源扩展需求 (原 v01_source)
    │   ├── story-map.md                     ← 用户故事地图 (待补充)
    │   ├── nfr.md                           ← NFR 规格 (待拆分)
    │   ├── assumptions.md                   ← 假设登记表 (待拆分)
    │   ├── use-cases/                       ← 用例规约
    │   ├── bdd/                             ← BDD 场景 (.feature)
    │   └── decision-tables/                 ← 决策表
    │
    ├── spec/                                ← Phase 2: 功能规格
    │   ├── functional-spec.md               ← 基础功能规格
    │   └── functional-spec-source.md        ← 多源扩展规格 (原 v01_source)
    │
    ├── architecture/                        ← Phase 3: 技术设计
    │   ├── design-doc.md                    ← 基础技术设计
    │   ├── design-doc-source.md             ← 多源扩展设计 (原 v01_source)
    │   ├── impact-analysis.md               ← 变更影响分析 (待补充)
    │   ├── c4/                              ← C4 图 (现存于 design-doc.md)
    │   ├── views/                           ← 4+1 视图
    │   ├── contracts/                       ← API/函数契约
    │   └── observability/                   ← 可观测性设计
    │
    ├── features/                            ← Phase 4: 特性拆解
    │   ├── feature-list.md                  ← 基础特性清单
    │   └── feature-list-source.md           ← 多源扩展特性 (原 v01_source)
    │
    └── mvp/                                 ← Phase 5: MVP 交付
        ├── mvp-scope.md                     ← 基础 MVP 范围
        └── mvp-scope-source.md              ← 多源扩展 MVP (原 v01_source)
```

## 阅读指南

### 了解产品
1. `paper-agent-overview.md` — 产品定位 + 10 环节交互设计 + 路线图
2. `v01/idea-brief.md` — 项目全貌、愿景、范围、差距分析

### 了解需求与设计
3. `v01/requirements/requirement-doc.md` — 基础需求定义
4. `v01/requirements/requirement-doc-source.md` — 多源扩展需求
5. `v01/spec/functional-spec.md` — 功能规格
6. `v01/architecture/design-doc.md` — 技术设计
7. `architecture/adr/` — 关键架构决策

### 了解旅程
8. `v01/journeys/user-journey.md` — 用户旅程 + 错误恢复
9. `v01/journeys/developer-journey.md` — 开发者旅程

### 了解实现与验证
10. `v01/features/feature-list.md` — 特性视图
11. `v01/mvp/mvp-scope.md` — MVP 范围
12. `v01/traceability-matrix.md` — 需求追溯

### 知识沉淀
- `project-knowledge/` — 决策、事故、模式、反模式归档
- `glossary.md` — 领域术语表

## 方法论阶段映射

| 阶段 | 主要文档 | 状态 |
|------|---------|------|
| Phase 0 想法澄清 | `v01/idea-brief.md`, `glossary.md`, `v01/journeys/user-journey.md` | ✅ 完成 |
| Phase 1 需求定义 | `v01/requirements/requirement-doc.md`, `v01/traceability-matrix.md` | ✅ 完成 |
| Phase 2 功能规格 | `v01/spec/functional-spec.md` | ✅ 完成 (BDD 待补) |
| Phase 3 技术设计 | `v01/architecture/design-doc.md`, `architecture/adr/` | ✅ 完成 (契约待补) |
| Phase 4 特性拆解 | `v01/features/feature-list.md` | ⚠️ 格式待对齐 |
| Phase 5 MVP 交付 | `v01/mvp/mvp-scope.md`, `paper_agent/` 代码 | ✅ 已实现 |
| **v02 — Workspace Layer** | | |
| Phase 0 用户旅程 | `v02/journeys/user-journey.md` | ✅ 完成 |
| Phase 1 需求定义 | `v02/requirements/requirement-doc.md` | ✅ 完成 |
| Phase 2 功能规格 | `v02/spec/functional-spec.md` | ✅ 完成 |
| Phase 3 技术设计 | `v02/architecture/design-doc.md`, `architecture/adr/ADR-004` | ✅ 完成 |
| Phase 4 特性拆解 | `v02/features/feature-list.md` | ✅ 完成 |
| Phase 5 实现 | `paper_agent/` 代码 | ✅ 已实现 |

## 版本说明

- **v01/** — 基础版本 + 多源扩展（原 `v01_source` 已合并）
  - 基础文件：`requirement-doc.md`, `functional-spec.md`, `design-doc.md` 等
  - 多源扩展：带 `-source` 后缀的文件（`requirement-doc-source.md` 等）

- **v02/** — Workspace Layer + 精确查找
  - 引入 `.paper-agent/` Workspace 目录（阅读管理、笔记、分组、引用链、仪表盘）
  - 新增 `paper_find_and_download` 按标题多源精确查找 + 下载
  - 新增 `paper_workspace_status` 人可读仪表盘
  - Workspace 初始化由 `paper-agent setup` CLI 自动完成，MCP 工具静默 auto-init

```
docs/v02/
├── requirements/
│   └── requirement-doc.md        ← Phase 1: v02 需求
├── spec/
│   └── functional-spec.md        ← Phase 2: v02 功能规格
├── architecture/
│   └── design-doc.md             ← Phase 3: v02 技术设计
├── features/
│   └── feature-list.md           ← Phase 4: v02 特性清单
└── journeys/
    └── user-journey.md           ← Phase 0: v02 用户旅程
```
