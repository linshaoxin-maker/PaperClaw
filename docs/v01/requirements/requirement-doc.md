# Paper Agent Requirement Doc

**Title:** Paper Agent Requirement Definition Document
**Version:** v01
**Status:** Draft
**Owner:** Paper Agent Team
**Last Updated:** 2026-03-10

## Related Documents
- [Feature](./feature.md)
- [Specification](./spec.md)
- [Design](./design.md)
- [MVP](./mvp.md)

---

# 1. 【Requirement Doc】

## 1.1 背景
AI Researchers、Research Engineers 与 Automation Agents 需要持续获取与当前研究方向、实现任务、实验设计相关的论文信息。但现有论文获取方式通常依赖人工浏览 arXiv、会议页面或零散搜索工具，存在效率低、噪声高、复用差、难以接入自动化工作流的问题。

Paper Agent 旨在成为一个 **CLI-first 的 paper intelligence system**，用于持续收集论文、语义筛选、生成 digest、支持检索与主题梳理，并向人类用户与自动化 agent 提供可复用的研究上下文。

## 1.2 问题陈述
当前用户在论文获取与使用流程中面临以下核心问题：

1. **发现成本高**：每天新增论文数量过大，人工筛选成本高。
2. **信噪比低**：基于关键词的简单过滤难以准确识别高价值论文。
3. **研究工作流割裂**：论文发现、阅读、检索、实现、总结分散在多个工具中。
4. **历史发现难复用**：看过的论文难以被结构化保存与二次检索。
5. **自动化支持弱**：现有方案难以稳定接入 Cursor、Codex、shell workflow 等 agent 场景。

## 1.3 目标
本需求文档定义 Paper Agent v01 的需求目标如下：

1. 提供以 **Digest 为默认入口** 的论文日常 intake 机制。
2. 支持从选定来源自动收集论文并构建本地 paper library。
3. 支持基于语义理解的 relevance filtering 与 topic tagging。
4. 支持以 **Search 为基础检索层** 的 query / QA / topic exploration 工作流。
5. 支持 paper detail、topic report 等可复用研究对象。
6. 支持通过 CLI + JSON 让 Cursor/Codex/agent 稳定消费输出结果。

## 1.4 非目标
以下内容不属于 v01 Requirement 范围：

1. 作为完整 reference manager 替代品。
2. 作为通用笔记、批注、知识库平台。
3. 以 PDF 全文解析与全文理解作为核心依赖。
4. 社交协作、评论讨论、社区互动能力。
5. 移动端优先体验。
6. 付费/受保护内容的抓取与处理。
7. 完整 scholarly graph / citation graph exploration。

## 1.5 目标用户

### Primary Users
- **Individual AI Researcher**：需要低成本持续跟踪研究方向。
- **Research Engineer**：需要在实现、复现、benchmark、设计阶段快速取回论文上下文。
- **PhD Student / Early Researcher**：需要快速建立 topic understanding 并维护本地知识积累。

### Secondary Users
- **Research Team**：希望形成较统一的论文监控与梳理方式。
- **Automation Agents**：需要通过 CLI/JSON 稳定获取 digest、query result、paper detail、topic report。

## 1.6 关键场景

### 场景 S1：首次初始化并跑通系统
用户首次安装后，通过模板与最小配置快速完成 setup，并成功得到第一份 digest。

### 场景 S2：每日查看精选论文
系统每日自动收集与筛选论文，生成 digest 供用户快速浏览高信号论文。

### 场景 S3：围绕具体问题检索论文
用户针对一个技术问题、研究问题或实现任务发起查询，系统返回结构化结果。

### 场景 S4：围绕某个 topic 做系统性梳理
用户希望从一个主题切入，获取按 subtopic 组织的 topic report。

### 场景 S5：被外部 agent 调用
Cursor/Codex 等 agent 在编码、规划、citation、benchmark 场景下调用 Paper Agent 获取研究上下文。

### 场景 S6：基于方法相似性发现论文
用户阅读到一篇使用某种技术手段的论文，希望找到使用类似方法的其他论文，以评估该方法的广泛性或寻找改进方向。

### 场景 S7：基于解决目标发现论文
用户面对一个具体研究问题，希望找到所有试图解决该问题的论文，不论它们采用何种方法。

### 场景 S8：生成文献综述
用户围绕一个研究问题或方法方向，希望系统自动生成一篇结构化综述，涵盖方法分类、对比分析、研究趋势与空白。

## 1.7 需求清单

### 1.7.1 功能需求

#### FR-01 初始化与模板启动
**描述**：系统应支持通过模板 + 最小配置快速完成初始化。
**成功标准**：用户无需编辑代码即可完成初始化，并在首次运行后获得一份可读 digest。

#### FR-02 论文收集
**描述**：系统应支持从配置来源收集论文，并形成本地 library。
**成功标准**：用户可触发自动或手动收集，且收集结果可在本地库中查询。

#### FR-03 语义筛选
**描述**：系统应支持根据用户兴趣对论文进行 relevance filtering。
**成功标准**：系统可为论文生成 relevance 判断，并将高价值论文优先纳入 digest。

#### FR-04 Topic 标注
**描述**：系统应支持为论文生成 topic/tag。
**成功标准**：论文结果中可见结构化 topic 信息，并可用于 digest、search、report。

#### FR-05 Digest 生成
**描述**：系统应生成 digest 作为默认日常入口。
**成功标准**：digest 至少包含基础元数据、推荐理由、统计摘要，并支持用户快速消费。

#### FR-06 Digest 后续动作
**描述**：用户在 digest 后应能继续执行下一步研究动作。
**成功标准**：digest 中涉及的论文可进一步进入 paper detail、search、辅助 inbox 或 agent handoff 流程。

#### FR-07 Search 基础检索
**描述**：系统应提供 search 作为 retrieval base layer。
**成功标准**：用户可基于 query 从本地库中检索相关论文，结果可被上层流程复用。

#### FR-08 结构化问题回答
**描述**：系统应在 search 之上支持 question-answering 型输出。
**成功标准**：对研究问题可返回结构化回答，并给出支撑论文。

#### FR-09 Topic 梳理与聚类
**描述**：系统应在 search 之上支持 topic organization / clustering。
**成功标准**：用户可获得按 subtopic 组织的结构化结果。

#### FR-10 Paper Detail
**描述**：系统应支持单篇论文的深度详情视图。
**成功标准**：paper detail 至少包含核心元数据、推荐解释、关联上下文、可导出表示。

#### FR-11 Topic Report Artifact
**描述**：系统应支持生成可保存、可复用、可被 agent 消费的 topic report。
**成功标准**：topic report 可作为独立产物存在，而非仅为临时输出。

#### FR-12 Agent Consumable Outputs
**描述**：系统应允许 agent 程序化访问 digest、query result、paper detail、topic report。
**成功标准**：以上四类对象均可通过稳定 CLI + JSON 方式获取。

#### FR-13 Context-Aware Retrieval
**描述**：系统应支持基于文件、任务、代码上下文的检索扩展能力。
**成功标准**：agent 或用户提供上下文后，系统可生成相应的 research retrieval 结果。

#### FR-14 基于方法相似性的论文发现
**描述**：系统应支持从一篇论文或一段方法描述出发，找到使用类似方法/技术手段的论文。
**成功标准**：用户提供论文或方法描述后，系统返回方法维度上相似的论文集合，而非仅按 topic 或关键词匹配。

#### FR-15 基于解决目标的论文发现
**描述**：系统应支持从一个研究目标或问题描述出发，找到试图解决相同或相似目标的论文，不限于使用相同方法。
**成功标准**：用户提供目标描述后，系统返回研究目标维度上相关的论文集合，并可与方法维度正交组合。

#### FR-16 文献综述生成
**描述**：系统应支持基于检索到的论文集合，生成结构化文献综述，覆盖问题定义、方法分类学、对比分析、研究空白与未来方向。
**成功标准**：综述可作为独立 artifact 保存与复用，深度和结构化程度高于 topic report，接近可辅助研究写作的 survey 草稿。

### 1.7.2 业务规则

#### BR-01 默认主入口
**规则**：系统默认主入口必须是 Digest，而非 inbox、search 或 agent-only 模式。
**成功标准**：用户日常使用时，digest 被定义为默认 intake surface。

#### BR-02 首次成功定义
**规则**：首次 setup 成功的判定标准是“拿到第一份可读且有价值的 digest”。
**成功标准**：系统验收时，以 digest 产出作为首次跑通标准。

#### BR-03 Digest 数量策略
**规则**：digest 默认规模应倾向 Top 20，同时支持数量可配置。
**成功标准**：用户可调整 digest 数量，默认值不低于支撑日常 intake 的合理规模。

#### BR-04 Digest 质量策略
**规则**：digest 应高置信优先，不得仅为凑满数量而降低质量。
**成功标准**：digest 至少支持高置信区与低置信补充区的区分。

#### BR-05 Search 层级关系
**规则**：Search 是 retrieval base layer；QA 与 topic exploration 建立在其上。
**成功标准**：需求与规格中明确 search 为底层、QA/report 为上层综合能力。

#### BR-06 Inbox 定位
**规则**：Inbox 仅为辅助能力，不是默认主入口。
**成功标准**：需求文档中将 inbox 定义为 digest 后续处理区而非 primary surface。

### 1.7.3 非功能需求

#### NFR-REQ-01 可用性
**描述**：用户应能通过模板和最小配置快速跑通系统。
**成功标准**：首次 setup 不依赖代码修改或复杂手工配置。

#### NFR-REQ-02 可解析性
**描述**：面向 agent 的输出必须稳定、结构化、可解析。
**成功标准**：CLI 输出支持 JSON，且结构稳定可消费。

#### NFR-REQ-03 可复用性
**描述**：核心结果对象应可保存和后续复用。
**成功标准**：digest、query result、paper detail、topic report 均可作为稳定对象存在。

#### NFR-REQ-04 可测量性
**描述**：需求必须可验证。
**成功标准**：每条关键需求均可通过输出结果、行为表现或量化指标进行验收。

## 1.8 范围（In / Out）

### In Scope
- 模板化初始化与最小配置启动
- 来源论文收集与本地 library
- relevance filtering 与 topic tagging
- digest-first workflow
- search-based retrieval
- structured QA
- topic clustering / topic report
- paper detail
- agent-consumable outputs
- context-aware retrieval
- 基于方法相似性的论文发现
- 基于解决目标的论文发现
- 文献综述生成

### Out of Scope
- UI 页面细节与按钮交互
- API 设计与 DB schema
- PDF 全文深度解析（方法与目标提取基于 title + abstract）
- 引文网络深度分析
- 社交协作能力
- 通用知识管理与笔记系统

## 1.9 优先级（Must / Should / Could）

### Must
- FR-01 初始化与模板启动
- FR-02 论文收集
- FR-03 语义筛选
- FR-05 Digest 生成
- FR-07 Search 基础检索
- FR-10 Paper Detail
- FR-11 Topic Report Artifact
- FR-12 Agent Consumable Outputs
- BR-01 默认主入口
- BR-02 首次成功定义
- BR-05 Search 层级关系

### Should
- FR-04 Topic 标注
- FR-06 Digest 后续动作
- FR-08 结构化问题回答
- FR-09 Topic 梳理与聚类
- FR-13 Context-Aware Retrieval
- FR-14 基于方法相似性的论文发现
- FR-15 基于解决目标的论文发现
- FR-16 文献综述生成
- BR-03 Digest 数量策略
- BR-04 Digest 质量策略
- BR-06 Inbox 定位

### Could
- 更丰富的模板体系
- 更细粒度的 digest 分区策略
- 更多可导出格式
- [待确认] 更复杂的 team workflow 支持

## 1.10 成功指标

### 用户成功指标
- 用户能把 digest 作为默认 daily intake surface 使用。
- 用户认为 digest 中高置信内容有明显价值。
- 用户可在实现/研究过程中复用 paper detail、query result、topic report。

### 产品成功指标
- 首次 setup 后可成功产出 digest。
- Search 能支撑上层 QA、topic report 与 survey。
- Topic report 能以独立 artifact 形式保存与复用。
- Survey 能以独立 artifact 形式保存与复用，深度高于 topic report。
- 方法相似性检索能返回技术手段上真正相似的论文。
- 目标相似性检索能返回跨方法的同目标论文。
- agent 可稳定获取五类对象：digest、query result、paper detail、topic report、survey。

### 量化成功指标
- 高置信 digest precision > 90%。
- Typical search latency < 1s。
- Typical automation query latency < 2s。
- Scheduled collection 可持续运行而无需频繁人工介入。

## 1.11 依赖项
- 论文来源（如 arXiv / conference metadata source）
- LLM provider 作为语义筛选与综合能力支撑
- 本地 CLI 运行环境
- [待确认] topic report 是否要求默认依赖在线模型能力

## 1.12 风险项
- **筛选精度风险**：如果 relevance 判断不稳定，digest 价值会下降。
- **成本风险**：LLM 调用成本过高会削弱持续使用可行性。方法/目标提取与综述生成会进一步增加 LLM 调用量。
- **自动化稳定性风险**：若 JSON 输出或命令行为不稳定，agent integration 价值下降。
- **topic synthesis 风险**：topic report 若组织质量不足，会影响其作为 artifact 的可信度。
- **方法提取精度风险**：基于 title + abstract 的方法提取可能遗漏细粒度方法信息，影响方法相似性检索质量。
- **综述深度风险**：综述若组织质量不足或方法对比过于表面，可能无法满足研究写作辅助的期望。
- **范围膨胀风险**：若过早扩展到全文解析、协作、复杂知识库，会偏离 v01 目标。

---

# 2. 【用例规约】

## UC-01 首次初始化并获得首份 Digest
- **UC-ID**：UC-01
- **参与者**：Individual AI Researcher / Research Engineer
- **前置条件**：用户已安装系统；具备基本运行环境。
- **后置条件**：系统已保存基础配置，生成首份 digest。
- **主流程**：
  1. 用户启动初始化流程。
  2. 用户选择模板（研究方向模板和/或来源模板）。
  3. 用户填写最小必要配置。
  4. 系统执行收集与筛选。
  5. 系统生成第一份 digest。
  6. 用户查看 digest，确认系统已跑通。
- **扩展流程**：
  - E1：用户跳过模板，改用最小配置直接启动。
  - E2：首次 digest 结果不理想，用户后续调整配置重跑。
  - E3：[待确认] 若来源为空或模板不可用，系统是否提供默认研究方向模板。
- **成功标准**：用户获得一份可读且可用于继续研究工作的 digest。

## UC-02 每日查看 Digest
- **UC-ID**：UC-02
- **参与者**：Individual AI Researcher / PhD Student
- **前置条件**：系统已完成论文收集与筛选；存在可生成 digest 的数据。
- **后置条件**：用户完成对当日高信号论文的初步 intake。
- **主流程**：
  1. 系统按计划完成论文收集。
  2. 系统执行 relevance filtering 与 topic tagging。
  3. 系统生成 digest。
  4. 用户查看 digest。
  5. 用户基于 digest 做下一步动作。
- **扩展流程**：
  - E1：用户打开某篇 paper detail。
  - E2：用户围绕 digest 中某个方向继续 search。
  - E3：用户将论文放入辅助 inbox / queue。
  - E4：用户将结果交给 agent 消费。
- **成功标准**：digest 能帮助用户以低成本识别高价值论文。

## UC-03 针对问题进行结构化查询
- **UC-ID**：UC-03
- **参与者**：Research Engineer / Individual AI Researcher
- **前置条件**：本地 paper library 已存在可检索数据。
- **后置条件**：用户获得结构化回答或相关结果集合。
- **主流程**：
  1. 用户输入研究问题、技术问题或 topic query。
  2. 系统执行 search 作为基础检索。
  3. 系统在检索结果上生成结构化回答或聚类结果。
  4. 用户查看结果并决定下一步。
- **扩展流程**：
  - E1：用户仅需要 ranked retrieval 结果。
  - E2：用户转入某篇 paper detail。
  - E3：[待确认] 若本地结果不足，系统是否允许提示需要扩大来源范围。
- **成功标准**：系统输出不只是论文列表，而是可支持研究决策的结构化结果。

## UC-04 生成 Topic Report
- **UC-ID**：UC-04
- **参与者**：PhD Student / Research Engineer / Research Team
- **前置条件**：本地 paper library 中存在相关 topic 的论文。
- **后置条件**：生成可保存与复用的 topic report artifact。
- **主流程**：
  1. 用户指定 topic。
  2. 系统检索相关论文。
  3. 系统按 subtopic 组织结果。
  4. 系统生成中等深度的 topic report。
  5. 用户查看、保存或复用 topic report。
- **扩展流程**：
  - E1：用户基于 topic report 继续向某个 subtopic 深挖。
  - E2：agent 读取 topic report 用于规划与实现。
  - E3：[待确认] 是否支持同一 topic 的多版本 report。
- **成功标准**：topic report 可作为独立研究产物被复用，而非一次性输出。

## UC-06 基于方法相似性发现论文
- **UC-ID**：UC-06
- **参与者**：Individual AI Researcher / Research Engineer
- **前置条件**：本地 paper library 中已有可检索论文；论文已完成方法维度的结构化提取。
- **后置条件**：用户获得方法维度上相似的论文集合。
- **主流程**：
  1. 用户提供一篇论文（通过 ID）或一段方法描述文字。
  2. 系统提取该论文或描述中的方法特征（technique、algorithm、framework 等）。
  3. 系统基于方法维度在本地库中检索相似论文。
  4. 系统返回按方法相似度排序的论文结果。
- **扩展流程**：
  - E1：用户从方法相似结果中进入 paper detail。
  - E2：用户基于方法相似结果继续生成综述。
  - E3：系统同时展示方法维度与目标维度的交叉结果。
- **成功标准**：返回结果确实在方法/技术手段上与输入相似，而不仅仅是 topic 重合。

## UC-07 基于解决目标发现论文
- **UC-ID**：UC-07
- **参与者**：Individual AI Researcher / PhD Student
- **前置条件**：本地 paper library 中已有可检索论文；论文已完成目标维度的结构化提取。
- **后置条件**：用户获得研究目标维度上相关的论文集合。
- **主流程**：
  1. 用户提供一个研究目标或问题描述。
  2. 系统提取目标特征并在本地库中检索解决类似目标的论文。
  3. 系统返回按目标相关度排序的论文结果，其中可能包含不同方法的论文。
  4. 用户查看结果并决定下一步。
- **扩展流程**：
  - E1：用户将结果按方法维度进一步聚类。
  - E2：用户基于结果生成文献综述。
  - E3：[待确认] 若本地结果不足，是否提示扩大来源。
- **成功标准**：返回结果涵盖解决同一问题的多种方法路径，而非仅限于某一种技术。

## UC-08 生成文献综述
- **UC-ID**：UC-08
- **参与者**：PhD Student / Research Engineer / Individual AI Researcher
- **前置条件**：本地 paper library 中存在足够数量的相关论文。
- **后置条件**：生成可保存与复用的文献综述 artifact。
- **主流程**：
  1. 用户指定综述切入点（可以是 topic、方法描述、研究目标，或其组合）。
  2. 系统检索相关论文，同时提取方法维度与目标维度的结构化信息。
  3. 系统按问题定义、方法分类学、对比分析、研究趋势、研究空白与未来方向组织综述。
  4. 系统生成综述 artifact。
  5. 用户查看、保存或复用综述。
- **扩展流程**：
  - E1：用户基于综述继续向某个方法子方向深挖。
  - E2：agent 读取综述用于研究规划或写作辅助。
  - E3：用户在综述基础上手动补充和编辑。
  - E4：[待确认] 是否支持综述的增量更新。
- **成功标准**：综述结构化程度和深度高于 topic report，可作为研究写作的起点。

## UC-05 Agent 调用稳定对象
- **UC-ID**：UC-05
- **参与者**：Automation Agent（Cursor / Codex / Shell Agent）
- **前置条件**：系统命令行可用；相关数据对象已存在或可生成。
- **后置条件**：agent 获得可解析对象并用于后续动作。
- **主流程**：
  1. Agent 发起调用。
  2. 系统根据请求返回 digest、query result、paper detail、topic report 或 survey。
  3. 返回结果为稳定、结构化输出。
  4. Agent 将结果用于 planning / coding / citation / benchmarking。
- **扩展流程**：
  - E1：Agent 基于文件/代码/任务上下文发起 context-aware retrieval。
  - E2：Agent 在 query result 后继续拉取 paper detail。
  - E3：Agent 在 query 之后触发 topic report 或 survey 生成。
  - E4：Agent 基于方法描述发起 method-similarity retrieval。
  - E5：Agent 基于目标描述发起 objective-based retrieval。
- **成功标准**：agent 能稳定、可组合地消费系统对象，而非依赖人工解释。

---

# 3. 【NFR 规格】

| NFR-ID | 类别 | 量化指标 | 测量方法 |
|---|---|---|---|
| NFR-01 | 性能 | Typical search latency < 1s | 在中等规模本地 library 上执行标准查询并记录响应时间 |
| NFR-02 | 性能 | Typical automation query latency < 2s | 在 CLI + JSON 场景下执行 agent 查询并统计响应时间 |
| NFR-03 | 质量 | 高置信 digest precision > 90% | 抽样评估 digest 中高置信论文的用户主观相关性判断 |
| NFR-04 | 可用性 | 首次 setup 可在模板 + 最小配置下成功跑通 | 按标准初始化流程测试是否可生成首份 digest |
| NFR-05 | 自动化兼容性 | 四类对象均可通过稳定结构化输出获取 | 对 digest/query result/paper detail/topic report 执行结构一致性检查 |
| NFR-06 | 可靠性 | Scheduled collection 可稳定运行且无需频繁人工介入 | 连续运行场景下统计失败率与人工干预频次 |
| NFR-07 | 可复用性 | Topic report 必须可保存并再次消费 | 验证 report 能被重复读取、引用或供 agent 使用 |
| NFR-08 | 可维护性 | 需求项均具备可验证成功标准 | 评审需求文档，检查每条关键需求是否存在验收定义 |

---

# 4. 【假设登记表】

| 假设 | 影响 | 确认状态 |
|---|---|---|
| 用户接受 CLI-first 作为主使用方式 | 若不接受，产品主入口设计需要调整 | 已确认 |
| 用户日常默认入口是 Digest | 直接影响核心 workflow 与优先级 | 已确认 |
| 首次成功以“拿到 digest”为标准 | 直接影响初始化验收标准 | 已确认 |
| Search 是 retrieval base layer，QA/report 建立在其上 | 直接影响需求结构与后续 spec 拆分 | 已确认 |
| Inbox 只是辅助能力，不是主入口 | 影响范围控制与功能优先级 | 已确认 |
| Digest 默认规模倾向 Top 20 | 影响 digest 默认策略 | 已确认 |
| Digest 应采用高低分区而非单纯凑满 Top N | 影响 digest 输出规则 | 已确认 |
| Topic report 是独立 artifact，而非临时视图 | 影响 report 的定位与验收方式 | 已确认 |
| Topic report 默认是中等深度 | 影响 report 输出预期 | 已确认 |
| Agent 需要消费 digest、query result、paper detail、topic report 四类对象 | 影响自动化接口需求 | 已确认 |
| Paper detail 需要包含推荐解释、关联上下文和导出能力 | 影响 detail 的信息深度定义 | 已确认 |
| 方法相似性与目标相似性检索基于 title + abstract 提取，不依赖 PDF 正文 | 影响提取精度与架构决策 | 已确认 |
| 方法维度与目标维度是正交的两个检索维度 | 影响 paper 对象索引设计 | 已确认 |
| 文献综述是 topic report 之上的更高级产物，不替代 topic report | 影响 artifact 层级关系与功能定位 | 已确认 |
| 综述结构应覆盖问题定义、方法分类学、对比分析、研究空白与未来方向 | 影响 survey 输出模板定义 | 已确认 |
| Agent 需要消费的稳定对象从四类扩展为五类（新增 survey） | 影响自动化接口需求 | 已确认 |
| [待确认] Topic report 是否必须依赖在线 LLM 才能生成 | 影响离线能力与依赖约束 | 待确认 |
| [待确认] 当本地库结果不足时，系统是否需要显式提示扩展来源 | 影响查询失败策略 | 待确认 |
| [待确认] 是否需要支持 topic report 多版本管理 | 影响 artifact 生命周期管理 | 待确认 |
| [待确认] 是否需要支持综述的增量更新 | 影响 survey artifact 生命周期管理 | 待确认 |

---

**Next Steps:** 基于本 Requirement Doc，对 [Specification](./spec.md) 做逐条映射，确保 Must/Should 项均有明确功能规约覆盖。
