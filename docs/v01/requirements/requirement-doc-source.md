# Paper Agent v01_source Requirement Doc

**Title:** Paper Agent v01_source Requirement Definition Document
**Version:** v01_source
**Status:** Draft
**Owner:** Paper Agent Team
**Last Updated:** 2026-03-12

## Related Documents
- Base Requirement (v01): `docs/v01/requirement.md`
- [Feature](./feature.md)
- [Specification](./spec.md)
- [Design](./design.md)
- [MVP](./mvp.md)

---

# 1. 【Requirement Doc - Source/Profile Extension】

## 1.1 背景

v01 的初始化（`paper-agent init`）倾向于要求用户在首次安装时就填写 `topics/keywords/sources`，并通过“立即产出第一份 digest”来定义首次成功。

但在真实使用中存在以下问题：

- **新手用户无法在 init 阶段就给出高质量兴趣描述**：研究方向可能仍在探索，或用户不知道如何把兴趣翻译成可用于检索/过滤的 topics 与 keywords。
- **来源范围与研究兴趣强耦合**：来源（arXiv 分类、会议/期刊）不只是“抓取参数”，也代表了用户的研究版图；应允许用户先把基础设施跑通，再逐步完善兴趣与来源。
- **单一来源覆盖不足**：仅依赖 arXiv 容易导致会议论文、领域核心 venue 覆盖不完整，影响 digest 与检索的完整性。

因此，本扩展将 v01 拆分为两段：

1. **基础设施初始化（init）**：只配置运行所需的基础设施（LLM provider、API key、基础数据目录等）。
2. **Profile 引导**：通过引导式流程（模板/AI/从已收集论文学习/手动）生成可迭代的 `topics/keywords`，并推荐、启用对应的数据源集合。

> 说明：v01 的 digest-first 原则不变，本扩展仅调整“首次成功”的路径，使其更适合从 0 到 1 的真实用户。

## 1.2 问题陈述（痛点）

1. **新手不知道如何描述研究兴趣**
   - 不清楚 topics 与 keywords 的粒度
   - 不知道写什么会导致高噪声/低召回

2. **只支持 arXiv 导致 coverage 不完整**
   - 会议（NeurIPS/ICLR/ICML/AAAI/IJCAI/ACL/EMNLP/NAACL）论文无法系统收集
   - 某些领域在 DBLP/ACL Anthology/OpenReview 上更权威或更新更及时

3. **数据源缺乏可配置/可推荐/可追踪**
   - 用户无法清晰看到“目前启用了哪些源、为什么启用、抓取是否成功、失败能否恢复”
   - 无法将“source”作为一等概念在 CLI 中管理

## 1.3 目标

在 v01 基础上新增目标（增量）：

- **G-SRC-01**：将 init 与 Profile 解耦：init 只完成基础设施配置，不强迫立即填写 topics/keywords/sources。
- **G-SRC-02**：提供 Profile 引导，帮助用户建立可用且可迭代的研究档案（topics/keywords + 偏好）。
- **G-SRC-03**：提供 Source Registry 与 Source 管理命令，让来源可列举、可启用/禁用、可推荐、可追踪。
- **G-SRC-04**：实现真正的多源抓取与入库（arXiv + OpenReview + DBLP + ACL Anthology），并提供可恢复的失败处理。

与 v01 保持一致的目标（引用 base）：
- Digest-first intake
- Search 为 retrieval base layer
- CLI + JSON 可被 agent 稳定消费

## 1.4 非目标

本扩展不在 v01_source 范围内的内容：

1. GUI / Web UI
2. 完整 citation graph / scholarly graph
3. 付费/受保护内容抓取
4. 引入重量级数据管线（队列、分布式调度器）
5. 对所有来源做统一全文 PDF 抓取与解析
6. 复杂的 team 权限/共享库
7. PapersWithCode / Semantic Scholar / Crossref 等扩展源（可后续版本）

## 1.5 关键场景（新增 Sx）

> v01 场景见 `docs/v01/requirement.md`。本节只定义增量场景。

### Sx-01：基础设施 init（仅 LLM）
- 用户首次安装时仅配置 LLM provider + API key + 基础路径，系统进入“已初始化但未完成 profile”的状态。

### Sx-02：profile create 引导生成 topics/keywords + 推荐 sources
- 用户执行 `paper-agent profile create`，从模板/AI/从论文学习/手动入口进入。
- 系统生成候选 topics/keywords，并给出推荐 sources（会议 + arXiv 分类 + 其他）。
- 用户可确认/回退/编辑后保存。

### Sx-03：sources list/enable/disable/add/config
- 用户通过 `paper-agent sources ...` 查看已知来源，启用/禁用来源，或添加自定义来源配置。

### Sx-04：collect 多源抓取并去重入库
- 用户执行 `paper-agent collect`。
- 系统按启用 sources 并发/分页抓取，去重入库。
- 单源失败不阻断整体流程，输出结构化错误摘要并支持重试。

## 1.6 Traceability（与 v01 的关系）

- 本扩展不改变 v01 的核心 workflow（Digest/Search/Artifact），只改变：
  - init 的强制字段
  - 增加 Profile 与 Source Registry 作为新的入口与基础能力
  - 多源 collection 的实现

| v01 Requirement | v01_source Extension | 关系 |
|---|---|---|
| FR-01 初始化与模板启动 | FR-SRC-01 基础设施 init（LLM-only） | 拆分/重构 |
| FR-02 论文收集 | FR-SRC-05 多源 collect | 扩展 |
| NFR-REQ-01 可用性 | FR-SRC-02 Profile 引导 | 增强 |
| NFR-REQ-06 可靠性 | FR-SRC-08 错误恢复 | 增强 |

## 1.7 需求清单（新增命名空间，避免与 v01 冲突）

### 1.7.1 功能需求

#### FR-SRC-01 基础设施 init（LLM-only）
**描述**：系统应支持仅配置 LLM 与基础路径完成初始化。
**成功标准**：init 不要求立即填写 topics/keywords/sources；配置状态明确标记“profile 未完成”。

#### FR-SRC-02 Profile 引导（多起点）
**描述**：系统应提供 `profile create` 引导生成 topics/keywords，并允许用户从多种入口开始。
**入口**：模板 / AI 分析 / 从已收集论文学习 / 手动。
**成功标准**：用户能在 1 次交互内得到可用的 topics/keywords，并可保存为 profile。

#### FR-SRC-03 Source Registry
**描述**：系统应内置来源定义（如 arXiv 分类、OpenReview venue、DBLP venue_key、ACL Anthology venue），并允许用户添加自定义源。
**成功标准**：来源可被列举与查看；启用状态可持久化。

#### FR-SRC-04 Source 推荐
**描述**：系统应基于领域模板规则推荐 sources；可选地支持 LLM 推荐作为补充。
**成功标准**：用户在 profile 流程中可看到推荐 sources 列表并选择启用。

#### FR-SRC-05 多源 collect（arXiv/OpenReview/DBLP/ACL Anthology）
**描述**：系统应支持从至少以下来源抓取并入库：arXiv、OpenReview、DBLP、ACL Anthology。
**成功标准**：每个来源均有真实抓取/解析/入库实现（不是仅配置占位）。

#### FR-SRC-06 Source 管理命令（list/show/enable/disable/add/config）
**描述**：系统应提供来源管理 CLI。
**成功标准**：用户能通过 CLI 完成来源浏览、启用/禁用、增加自定义源配置。

#### FR-SRC-07 `paper-agent config` 支持配置 sources/profile（命令式）
**描述**：系统应支持通过命令式接口更新 sources/profile（可作为 `config` 下的子命令或与 `sources/profile` 命令协作）。
**成功标准**：无需手动编辑 YAML 即可完成关键配置变更。

#### FR-SRC-08 错误恢复
**描述**：多源 collect 中单源失败不阻断整体流程；失败应结构化输出并允许重试。
**成功标准**：collect 输出包含 per-source 状态与错误摘要；整体返回码反映“部分失败”。

### 1.7.2 非功能需求（NFR）

| NFR-ID | 类别 | 描述 | 量化/验收 |
|---|---|---|---|
| NFR-SRC-01 | 性能 | 支持分页与并发抓取 | 在典型配置下可完成多源分页抓取且不显著阻塞 CLI |
| NFR-SRC-02 | 可靠性 | 单源失败不阻断、可重试 | collect 可输出部分失败并可再次执行补齐 |
| NFR-SRC-03 | 可配置性 | sources 可启用/禁用并持久化 | sources 状态在多次运行间保持一致 |
| NFR-SRC-04 | 可测试性 | adapters/registry 可被 mock | 单测可在无网络下运行 |

---

# 2. 【用例规约】

## UC-SRC-01 init（LLM-only）
- **UC-ID**：UC-SRC-01
- **参与者**：未初始化用户
- **前置条件**：用户已安装 CLI
- **后置条件**：配置文件写入成功；系统状态为“initialized=true, profile_completed=false”
- **主流程**：
  1. 用户执行 `paper-agent init`
  2. 系统仅询问 LLM provider / api key / model（以及必要路径）
  3. 系统写入配置并提示下一步运行 `paper-agent profile create`
- **成功标准**：init 不要求 topics/keywords/sources

## UC-SRC-02 profile create
- **UC-ID**：UC-SRC-02
- **参与者**：已初始化用户
- **前置条件**：已完成 UC-SRC-01
- **后置条件**：profile 写入配置；sources 启用状态写入配置或覆盖文件
- **主流程**：
  1. 用户执行 `paper-agent profile create`
  2. 用户选择入口：模板 / AI / 从论文学习 / 手动
  3. 系统生成 topics/keywords 候选并请求确认
  4. 系统基于 profile 推荐 sources
  5. 用户选择启用 sources 并保存
- **扩展流程**：
  - E1：用户回退到上一步重选入口
  - E2：用户手动编辑 topics/keywords
  - E3：[待确认] 若无 LLM（或 LLM 不可用），是否允许纯手动完成

## UC-SRC-03 sources configure
- **UC-ID**：UC-SRC-03
- **参与者**：已初始化用户
- **前置条件**：已完成 UC-SRC-01
- **后置条件**：sources 启用状态更新
- **主流程**：
  1. 用户执行 `paper-agent sources list`
  2. 用户查看 `paper-agent sources show <id>`
  3. 用户执行 `paper-agent sources enable/disable <id...>`
  4. （可选）用户执行 `paper-agent sources add` 添加自定义源定义

## UC-SRC-04 collect multi-source
- **UC-ID**：UC-SRC-04
- **参与者**：已 profile 用户 / 探索用户
- **前置条件**：已完成 UC-SRC-01；sources 有启用项
- **后置条件**：论文写入本地库；collection record 记录每源统计与错误
- **主流程**：
  1. 用户执行 `paper-agent collect`
  2. 系统读取启用 sources 并逐源抓取
  3. 系统去重入库（canonical_key）
  4. 系统输出 per-source collected/new/duplicate/error summary
- **扩展流程**：
  - E1：单源失败，整体仍返回部分成功
  - E2：未 profile 用户执行 collect，系统提示 `--explore` 或引导 profile

---

# 3. 【假设登记表】

| 假设 | 影响 | 确认状态 |
|---|---|---|
| init 与 profile 解耦可提升首次可用性 | 需改动 config validate 与 CLI init | 已确认 |
| sources 是一等概念，需要 registry 管理 | 需要 sources.yaml 与覆盖策略 | 已确认 |
| MVP 必须实现多源抓取入库 | 需实现 4 个 adapters 并做去重合并 | 已确认 |
| [待确认] OpenReview 的 venue/invitation 稳定性 | 影响抓取策略鲁棒性 | 待确认 |
| [待确认] ACL Anthology 可用数据格式与解析鲁棒性 | 影响 adapter 实现 | 待确认 |
| [待确认] DBLP 缺 abstract 的最小可用策略 | 影响 filtering/digest 的降级行为 | 待确认 |
| [待确认] sources.yaml 覆盖合并策略落在 config.yaml 还是独立文件 | 影响可维护性与 UX | 待确认 |
