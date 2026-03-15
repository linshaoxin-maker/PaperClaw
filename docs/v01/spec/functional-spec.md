# Functional Spec（功能规格说明）

## 1. 基本信息
- 功能名称：Paper Agent v01 Functional Spec
- 对应 Requirement：[Requirement Doc](./requirement.md)
- 文档负责人：Paper Agent Team
- 日期：2026-03-10
- 版本：v01
- 状态：草稿

---

## 2. 功能概述
> 本文档定义 Paper Agent v01 的功能规格，覆盖 digest-first intake、paper collection、semantic filtering、search-based retrieval、structured QA、topic report、paper detail、agent-consumable outputs 等功能行为。本文档关注功能层面的输入、触发、流程、规则、异常、验收，不描述数据库、缓存、队列等内部实现。

填写：
- 功能简介：
  - Paper Agent 是一个 CLI-first 的 paper intelligence system。
  - 它帮助用户从研究方向与来源模板快速启动，持续收集论文，进行语义筛选，产出 digest，并支持围绕问题、topic、代码上下文继续检索和综合。
  - 系统还应支持 paper detail 与 topic report 两类可复用对象，并向人类用户与 automation agent 提供稳定输出。
- 对应需求目标：
  - 以 Digest 作为默认 daily intake surface。
  - 以 Search 作为 retrieval base layer，支撑 QA 与 topic exploration。
  - 输出可被人类直接消费，也可被 agent 程序化消费。
- 本功能在整体流程中的位置：
  - 初始化 → 收集 → 筛选 → Digest → 后续探索（paper detail / search / inbox / agent）
  - Search → Structured QA / Topic Clustering → Topic Report
  - Agent 入口可直接消费 digest / query result / paper detail / topic report

---

## 3. 适用角色与权限
> 谁可以使用？谁不能使用？是否有权限差异？

填写：
- 角色 1：Individual AI Researcher
  - 是否可见：是
  - 是否可操作：是
  - 限制说明：可执行初始化、digest、search、paper detail、topic report、基础配置调整。
- 角色 2：Research Engineer
  - 是否可见：是
  - 是否可操作：是
  - 限制说明：除研究者功能外，更高频使用 query、paper detail、context-aware retrieval。
- 角色 3：PhD Student / Early Researcher
  - 是否可见：是
  - 是否可操作：是
  - 限制说明：更偏向 digest、topic report、topic exploration。
- 角色 4：Research Team
  - 是否可见：是
  - 是否可操作：部分可操作
  - 限制说明：v01 不定义团队级权限模型；团队场景按单用户工作流处理。[待确认]
- 角色 5：Automation Agent（Cursor / Codex / Shell Agent）
  - 是否可见：是
  - 是否可操作：是
  - 限制说明：主要通过 CLI + 结构化输出消费 digest、query result、paper detail、topic report；不要求交互式流程。
- 角色 6：未初始化用户
  - 是否可见：部分可见
  - 是否可操作：受限
  - 限制说明：不可完成 digest、query、topic report 等依赖配置与数据的流程；应被引导先初始化。

---

## 4. 用户入口与触发条件
> 用户从哪里进入这个功能，什么动作触发。

填写：
- 入口位置：
  - 初始化入口
  - digest 命令或 digest 文件
  - search/query 命令
  - paper detail 查看入口
  - topic report 生成入口
  - agent 通过 CLI 调用入口
- 触发动作：
  - 用户启动初始化
  - 用户触发 collection / digest / search / report / show
  - 定时任务触发 daily collection 与 digest
  - agent 基于任务、代码、文件上下文发起调用
- 前置条件：
  - 已安装可运行环境
  - 已完成初始化（除初始化流程本身外）
  - 已存在可用来源配置与基础兴趣配置
  - 需要检索/报告的场景下，本地库中应存在可用数据；如不存在则进入空状态或恢复引导
- 不满足前置条件时的表现：
  - 若未初始化：提示先完成初始化
  - 若无可用数据：提示先执行 collection 或调整来源配置
  - 若配置不完整：提示缺失项并引导补齐
  - 若 agent 调用缺少必要输入：返回结构化错误结果

---

## 5. 主流程
> 描述用户正常完成任务的标准流程。

### 主流程 1：首次初始化并拿到首份 Digest
1. 用户执行：启动初始化流程。
2. 系统响应：提示用户选择模板（研究方向模板和/或来源模板）并填写最小配置。
3. 用户继续：确认 topics、keywords、sources、LLM provider、基础偏好。
4. 系统完成：执行初次 collection 和 filtering，生成首份 digest，作为初始化成功结果。

### 主流程 2：每日查看 Digest
1. 用户执行：打开当日 digest 或触发 digest 生成。
2. 系统响应：返回 digest，包含统计摘要、推荐论文列表、推荐理由。
3. 用户继续：查看高置信区，必要时查看低置信补充区。
4. 系统完成：用户可从 digest 进入 paper detail、search、辅助 inbox 或 agent handoff。

### 主流程 3：围绕问题进行结构化查询
1. 用户执行：输入研究问题、技术问题或 topic query。
2. 系统响应：先执行 search 作为基础检索。
3. 用户继续：选择继续查看结构化回答、聚类结果或单篇详情。
4. 系统完成：输出结构化结果，并附支撑论文。

### 主流程 4：生成 Topic Report
1. 用户执行：发起 topic report 请求。
2. 系统响应：检索 topic 相关论文并按 subtopic 组织。
3. 用户继续：查看中等深度报告。
4. 系统完成：保存并返回 topic report artifact，可供后续复用。

### 主流程 5：基于方法相似性发现论文
1. 用户执行：提供一篇论文 ID 或一段方法描述文字。
2. 系统响应：提取方法特征（technique、algorithm、framework 等），在本地库中检索方法维度相似的论文。
3. 用户继续：查看按方法相似度排序的结果，选择进入 paper detail 或继续生成综述。
4. 系统完成：输出方法相似性检索结果，可被后续流程复用。

### 主流程 6：基于解决目标发现论文
1. 用户执行：输入一个研究目标或问题描述。
2. 系统响应：提取目标特征，在本地库中检索解决类似目标的论文。
3. 用户继续：查看按目标相关度排序的结果，结果中可能包含多种不同方法的论文。
4. 系统完成：输出目标相关检索结果，可被后续流程复用。

### 主流程 7：生成文献综述
1. 用户执行：指定综述切入点（topic、方法描述、研究目标或其组合）。
2. 系统响应：检索相关论文，提取方法维度与目标维度的结构化信息。
3. 用户继续：查看按问题定义、方法分类学、对比分析、研究趋势、研究空白、未来方向组织的综述。
4. 系统完成：保存并返回综述 artifact，可供后续复用与编辑。

### 主流程 8：Agent 消费系统对象
1. 用户执行：agent 发起 CLI 调用。
2. 系统响应：根据请求返回 digest、query result、paper detail、topic report 或 survey。
3. 用户继续：agent 对结果进行解析与后续动作。
4. 系统完成：返回稳定结构化结果，并支持进一步串联调用。

---

## 6. 分支流程
> 正常主流程外的分支情况。

### 分支场景 1：初始化时选择模板
- 触发条件：用户启动初始化。
- 用户行为：选择研究方向模板。
- 系统行为：填入默认方向相关的 topics、keywords 和建议来源。
- 最终状态：用户只需补齐最小必要配置后可继续。

### 分支场景 2：初始化时叠加来源模板
- 触发条件：用户希望从来源组合开始。
- 用户行为：选择来源模板。
- 系统行为：填入来源范围，并允许叠加研究方向模板。[待确认] 两者冲突时以用户最终确认内容为准。
- 最终状态：用户继续完成最小配置。

### 分支场景 3：Digest 后查看 Paper Detail
- 触发条件：用户在 digest 中发现感兴趣论文。
- 用户行为：进入 paper detail。
- 系统行为：返回论文核心详情、推荐解释、关联上下文、可导出信息。
- 最终状态：用户获得单篇论文的深度上下文。

### 分支场景 4：Digest 后继续 Search
- 触发条件：用户想围绕 digest 中某个方向继续探索。
- 用户行为：发起 query。
- 系统行为：执行 search，并返回 retrieval / QA / topic clustering 结果。
- 最终状态：用户进入更深一层的研究探索。

### 分支场景 5：Digest 后加入辅助 Inbox
- 触发条件：用户不想立即深读，但希望保留后续处理。
- 用户行为：将论文移入辅助 inbox / reading queue。
- 系统行为：将论文标记为后续处理对象。[待确认] v01 是否需要显式队列命名与分组。
- 最终状态：论文进入辅助处理路径。

### 分支场景 6：Query 输出结构化回答
- 触发条件：用户输入的是研究问题，而不是单纯关键词。
- 用户行为：请求围绕问题获取答案。
- 系统行为：在 search 结果之上生成结构化回答，并附支撑论文。
- 最终状态：用户获得面向决策的综合结果。

### 分支场景 7：Query 输出 Topic Clustering
- 触发条件：用户希望理解某个 topic 的内部结构。
- 用户行为：发起 topic-oriented query。
- 系统行为：返回按 subtopic 组织的结果集合。
- 最终状态：用户可继续生成 topic report。

### 分支场景 8：从论文出发发现方法相似论文
- 触发条件：用户在 digest 或 search 结果中发现一篇论文，想找方法类似的。
- 用户行为：以论文 ID 发起 method-similarity 查询。
- 系统行为：提取该论文的方法特征，检索方法维度相似论文。
- 最终状态：用户获得方法相似论文集合。

### 分支场景 9：从方法描述出发发现相似论文
- 触发条件：用户有一段方法描述文字，想找使用类似方法的论文。
- 用户行为：以文字描述发起 method-similarity 查询。
- 系统行为：从描述中提取方法特征，检索方法维度相似论文。
- 最终状态：用户获得方法相似论文集合。

### 分支场景 10：基于目标描述发现论文
- 触发条件：用户有一个研究目标或问题。
- 用户行为：输入目标描述发起 objective-based 查询。
- 系统行为：检索解决类似目标的论文，返回跨方法的结果。
- 最终状态：用户获得同目标跨方法的论文集合。

### 分支场景 11：从方法或目标检索结果生成综述
- 触发条件：用户在方法或目标检索后希望获得更深度的综合分析。
- 用户行为：发起 survey 请求。
- 系统行为：基于检索结果，组织综述结构，生成 survey artifact。
- 最终状态：用户获得可保存的综述 artifact。

### 分支场景 12：Agent 基于上下文发起调用
- 触发条件：agent 拥有任务描述、文件内容或代码上下文。
- 用户行为：agent 发起 context-aware retrieval。
- 系统行为：返回与上下文相关的 query result、paper detail、topic report 或 survey。
- 最终状态：agent 获得可继续串联消费的结构化对象。

---

## 7. 异常流程
> 失败、无权限、空数据、冲突等情况。

### 异常场景 1
- 场景名称：未初始化即请求 Digest
- 触发条件：用户未完成初始化就请求 digest。
- 系统处理：阻止生成 digest，提示先初始化。
- 用户提示：`尚未完成初始化。请先执行初始化流程，再生成 Digest。`
- 是否允许重试：是

### 异常场景 2
- 场景名称：本地库为空导致 Search 无结果
- 触发条件：用户执行 query，但本地库为空。
- 系统处理：返回空结果并提示先收集论文。
- 用户提示：`当前本地论文库为空。请先执行收集，或检查来源配置。`
- 是否允许重试：是

### 异常场景 3
- 场景名称：Topic Report 缺少足够数据
- 触发条件：相关 topic 的本地论文数量不足以形成报告。
- 系统处理：不生成正式 report，返回原因与建议动作。
- 用户提示：`当前主题相关论文不足，无法生成稳定 Topic Report。建议扩大来源或调整查询范围。`
- 是否允许重试：是

### 异常场景 4
- 场景名称：配置不完整
- 触发条件：用户缺少必要配置，例如来源或兴趣方向。
- 系统处理：中止当前流程，列出缺失项。
- 用户提示：`当前配置不完整：缺少来源或兴趣配置。请补齐后重试。`
- 是否允许重试：是

### 异常场景 5
- 场景名称：Agent 请求缺少必要输入
- 触发条件：agent 发起结构化调用，但未提供必要参数或上下文。
- 系统处理：返回结构化错误结果，不进入后续流程。
- 用户提示：`请求缺少必要输入，无法生成结果。请提供 query、对象类型或上下文。`
- 是否允许重试：是

### 异常场景 6
- 场景名称：方法提取无法识别有效方法特征
- 触发条件：用户提供的论文或描述中无法提取有效方法特征。
- 系统处理：返回提取失败提示，并建议用户提供更具体的方法描述。
- 用户提示：`无法从输入中提取有效方法特征。请提供更具体的方法或技术描述。`
- 是否允许重试：是

### 异常场景 7
- 场景名称：综述数据不足
- 触发条件：相关论文数量或方法多样性不足以生成有意义的综述。
- 系统处理：不生成正式综述，返回原因与建议动作。
- 用户提示：`当前相关论文不足，无法生成稳定综述。建议扩大来源或调整切入点。`
- 是否允许重试：是

### 异常场景 8
- 场景名称：结果不满足高置信条件
- 触发条件：digest 候选论文整体质量不足。
- 系统处理：优先展示高置信区；若高置信区不足，则显示低置信补充区并明确区分。
- 用户提示：`今日高置信论文较少，已附加低置信补充结果供参考。`
- 是否允许重试：否（用户可后续扩大来源或调低偏好）

---

## 8. 功能行为定义
> 逐条定义关键行为。这里要具体，但不进入技术实现。

### 功能点 1：模板化初始化
- 描述：支持用户通过模板快速起步。
- 触发方式：用户启动初始化流程。
- 系统行为：提供研究方向模板和来源模板，允许用户从模板进入最小配置。
- 完成条件：用户提交最小必要配置并成功得到首份 digest。
- 失败条件：缺少必要配置或初始化后无法产出 digest。

### 功能点 2：Digest 作为默认入口
- 描述：digest 是系统默认 daily intake surface。
- 触发方式：定时触发或用户触发 digest。
- 系统行为：生成包含统计摘要、推荐理由、基础元数据的 digest。
- 完成条件：用户能以 digest 作为每日查看高价值论文的入口。
- 失败条件：digest 为空、质量低、缺少关键信息、无法用于后续行动。

### 功能点 3：Digest 高低分区
- 描述：digest 应高置信优先，并区分低置信补充结果。
- 触发方式：系统生成 digest 时。
- 系统行为：先输出高置信区，再按规则决定是否展示低置信补充区。
- 完成条件：用户可明显区分高价值候选与探索性候选。
- 失败条件：结果混杂、无法判断置信差异，或仅为凑数而加入低价值内容。

### 功能点 4：Search 作为 Retrieval Base Layer
- 描述：search 为所有 deeper exploration 提供基础检索。
- 触发方式：用户或 agent 发起 query。
- 系统行为：返回基础检索结果，可被 QA、topic clustering、topic report 复用。
- 完成条件：query 能作为后续综合流程的起点。
- 失败条件：结果不可复用、过于原始、无法支撑上层流程。

### 功能点 5：结构化问题回答
- 描述：围绕研究问题返回结构化回答。
- 触发方式：用户输入问题型 query。
- 系统行为：基于 search 输出结构化答案，并给出支撑论文。
- 完成条件：结果可支持研究决策，而不只是展示 paper list。
- 失败条件：输出仅为无组织论文列表，无法回答问题。

### 功能点 6：Topic 聚类与 Topic Report
- 描述：围绕主题输出聚类结果并沉淀为 topic report。
- 触发方式：用户发起 topic exploration 或 report 请求。
- 系统行为：按 subtopic 组织论文，生成中等深度 report artifact。
- 完成条件：topic report 可保存、复用、供 agent 消费。
- 失败条件：输出过浅、无结构、不可复用。

### 功能点 7：Paper Detail
- 描述：提供单篇论文深度上下文。
- 触发方式：用户从 digest、search、agent follow-up 进入 paper detail。
- 系统行为：返回核心元数据、推荐解释、关联上下文、可导出信息。
- 完成条件：用户可基于 detail 做深入判断或导出使用。
- 失败条件：detail 信息过少，无法支持进一步使用。

### 功能点 8：方法相似性检索
- 描述：从论文或方法描述出发，找到方法维度上相似的论文。
- 触发方式：用户提供论文 ID 或方法描述文字。
- 系统行为：提取方法特征（technique、algorithm、framework），基于方法维度在本地库中检索并排序。
- 完成条件：返回结果确实在方法/技术手段上与输入相似。
- 失败条件：结果仅为 topic 重合而非方法层面相似，或无法提取有效方法特征。

### 功能点 9：目标相似性检索
- 描述：从研究目标或问题描述出发，找到试图解决类似目标的论文。
- 触发方式：用户输入目标描述。
- 系统行为：提取目标特征，在本地库中检索解决类似目标的论文，返回跨方法的结果。
- 完成条件：返回结果涵盖解决同一问题的多种方法路径。
- 失败条件：结果仅限于某一种技术路径，未能跨方法覆盖。

### 功能点 10：文献综述生成
- 描述：基于检索结果生成结构化文献综述，深度高于 topic report。
- 触发方式：用户发起 survey 请求，指定切入点。
- 系统行为：检索相关论文，提取方法与目标维度信息，按问题定义、方法分类学、对比分析、研究趋势、研究空白、未来方向组织综述。
- 完成条件：综述可作为独立 artifact 保存，结构化程度可辅助研究写作。
- 失败条件：综述过浅、缺少方法对比、无法识别研究空白。

### 功能点 11：Agent 可消费对象
- 描述：digest、query result、paper detail、topic report、survey 应可被 agent 消费。
- 触发方式：agent CLI 调用。
- 系统行为：返回稳定结构化结果，并支持进一步串联。
- 完成条件：agent 可稳定使用结果进行 planning、coding、citation 等任务。
- 失败条件：输出不稳定、不可解析或对象不完整。

---

## 9. 业务规则
> 排序、限制、默认值、优先级、冲突规则等。

填写：
- 规则 1：默认主入口必须是 Digest。
- 规则 2：首次成功标准必须是获得首份可读 digest。
- 规则 3：Digest 默认规模倾向 Top 20，且可配置。
- 规则 4：Digest 采用高置信优先策略，不得单纯为了凑数降低质量。
- 规则 5：Search 是 retrieval base layer；QA 与 topic report 建立在其上。
- 规则 6：Inbox 为辅助能力，不是主入口。
- 规则 7：Topic report 默认为中等深度，且是独立 artifact。
- 规则 8：Paper detail 默认包含核心详情、推荐解释、关联上下文、可导出信息。
- 规则 9：Agent 应可消费 digest、query result、paper detail、topic report、survey 五类对象。
- 规则 10：方法相似性与目标相似性是正交的两个检索维度，可独立使用也可组合。
- 规则 11：文献综述是 topic report 之上的更高级产物，不替代 topic report。
- 规则 12：方法与目标的结构化提取基于 title + abstract，不依赖 PDF 正文。

建议补充：
- 默认值：
  - Digest 默认规模：Top 20
  - Topic report 默认深度：中等深度
  - 默认工作流入口：Digest
- 优先级：
  - 高置信结果优先于低置信补充结果
  - 用户显式请求优先于默认展示规则
- 生效条件：
  - 初始化完成后生效所有日常流程
  - query / report 依赖本地库中存在可用数据
- 例外情况：
  - 若高置信结果不足，可显示低置信补充区
  - [待确认] 若 topic 数据不足，是否允许输出轻量 report 而非正式 report

---

## 10. 输入输出定义
> 站在功能层面定义，不写 API schema。

### 输入
- 输入项 1：初始化模板选择
  - 来源：用户
  - 是否必填：否
  - 约束：可选研究方向模板、来源模板或两者组合
- 输入项 2：最小配置
  - 来源：用户
  - 是否必填：是
  - 约束：至少包含 topics、keywords、sources、LLM provider、基础偏好
- 输入项 3：Query
  - 来源：用户或 agent
  - 是否必填：是
  - 约束：可以是研究问题、topic、检索短语、上下文输入
- 输入项 4：Topic 请求
  - 来源：用户或 agent
  - 是否必填：是（topic report 场景）
  - 约束：必须能表达一个可检索主题
- 输入项 5：Paper 选择
  - 来源：用户或 agent follow-up
  - 是否必填：是（paper detail 场景）
  - 约束：必须对应一篇已存在或已检索出的论文
- 输入项 6：上下文输入
  - 来源：agent 或用户
  - 是否必填：否
  - 约束：可为文件、代码、任务描述；若格式不可理解则进入异常流程
- 输入项 7：方法描述输入
  - 来源：用户或 agent
  - 是否必填：是（method-similarity 场景）
  - 约束：可以是论文 ID（系统从中提取方法）或自由文本方法描述
- 输入项 8：目标描述输入
  - 来源：用户或 agent
  - 是否必填：是（objective-based 场景）
  - 约束：必须能表达一个可理解的研究目标或待解决问题
- 输入项 9：综述切入点
  - 来源：用户或 agent
  - 是否必填：是（survey 场景）
  - 约束：可以是 topic、方法描述、研究目标或其组合

### 输出
- 输出项 1：Digest
  - 展示/返回内容：统计摘要 + 推荐论文列表 + 推荐理由 + 高低分区
  - 成功时表现：可作为每日主入口直接消费
  - 失败时表现：返回无数据/未初始化/配置不完整/结果质量不足等提示
- 输出项 2：Query Result
  - 展示/返回内容：retrieval result / structured QA / topic clustering
  - 成功时表现：支持进一步进入 paper detail 或 topic report
  - 失败时表现：返回空结果或错误引导
- 输出项 3：Paper Detail
  - 展示/返回内容：核心详情、推荐解释、关联上下文、可导出信息
  - 成功时表现：可支撑深入研究或 agent follow-up
  - 失败时表现：返回数据不存在或信息不足提示
- 输出项 4：Topic Report
  - 展示/返回内容：按 subtopic 组织的中等深度 report artifact
  - 成功时表现：可保存、复用、被 agent 消费
  - 失败时表现：返回数据不足或生成失败提示
- 输出项 5：Method-Similarity Result
  - 展示/返回内容：按方法相似度排序的论文列表 + 方法特征标签
  - 成功时表现：结果在方法维度上与输入相似
  - 失败时表现：返回方法提取失败提示或无结果引导
- 输出项 6：Objective-Based Result
  - 展示/返回内容：按目标相关度排序的论文列表 + 目标特征标签
  - 成功时表现：结果涵盖解决同一目标的多种方法路径
  - 失败时表现：返回无结果引导
- 输出项 7：Survey
  - 展示/返回内容：结构化综述 artifact，含问题定义、方法分类学、对比分析、研究趋势、研究空白、未来方向
  - 成功时表现：可保存、复用、被 agent 消费，深度高于 topic report
  - 失败时表现：返回数据不足或生成失败提示
- 输出项 8：结构化错误结果
  - 展示/返回内容：错误类型、原因说明、建议动作
  - 成功时表现：用户能根据引导回到正轨
  - 失败时表现：[待确认] 是否统一错误提示等级与分类编码

---

## 11. 状态与边界情况
> 明确各种状态下的用户可见行为。

### 状态定义
- 初始状态：尚未初始化，仅允许进入初始化流程。
- 加载中：正在执行 collection、digest、query、report、survey 等功能。
- 成功状态：获得有效 digest、query result、paper detail、topic report 或 survey。
- 空状态：当前无可用论文或 query 无结果。
- 部分成功：例如 digest 高置信区不足，但仍提供低置信补充区。
- 失败状态：配置错误、数据不足、输入不合法或流程无法完成。
- 权限不足：v01 暂不引入复杂权限模型；对未初始化用户按“不可操作”处理。[待确认]
- 数据不存在：请求的 paper 或 topic 在当前库中无法找到足够信息。
- 超限状态：[待确认] 若结果过多、topic 过宽或输入过长时的裁剪规则。

### 边界情况
- 边界情况 1：高置信论文少于 5 篇时，digest 仍可生成，但必须明确区分高低分区。
- 边界情况 2：query 能命中少量论文但不足以形成 topic report 时，只返回检索/聚类结果，不强制生成正式 report。
- 边界情况 3：用户提供研究方向模板但不补充个性化 keywords 时，系统可启动，但结果相关性可能下降。
- 边界情况 4：agent 只请求 paper detail 而没有先执行 search 时，若 paper 已可识别则直接返回，否则进入错误恢复。

---

## 12. 错误处理与用户提示
> 定义错误类别、提示方式、重试策略。

填写：
- 错误类型 1：未初始化
  - 触发条件：未完成初始化即请求 digest / search / report
  - 用户提示：`尚未完成初始化。请先执行初始化流程。`
  - 是否可重试：是
- 错误类型 2：配置不完整
  - 触发条件：缺少来源、topics、keywords 或 provider 等必要项
  - 用户提示：`当前配置不完整，请补齐必要配置后重试。`
  - 是否可重试：是
- 错误类型 3：本地库为空
  - 触发条件：执行 search / report 时无可用数据
  - 用户提示：`当前本地论文库为空。请先执行收集或检查来源配置。`
  - 是否可重试：是
- 错误类型 4：结果不足以支持 report
  - 触发条件：topic 数据量不足或相关性不足
  - 用户提示：`当前主题相关论文不足，暂无法生成稳定 Topic Report。建议扩大来源或调整查询。`
  - 是否可重试：是
- 错误类型 5：agent 输入不完整
  - 触发条件：缺少 query、对象类型或上下文
  - 用户提示：`请求缺少必要输入，无法生成结果。`
  - 是否可重试：是
- 错误类型 6：方法提取失败
  - 触发条件：输入的方法描述过于模糊或论文中无法提取有效方法特征
  - 用户提示：`无法从输入中提取有效方法特征。请提供更具体的方法或技术描述。`
  - 是否可重试：是
- 错误类型 7：综述数据不足
  - 触发条件：相关论文数量或方法多样性不足以生成有意义的综述
  - 用户提示：`当前相关论文不足，无法生成稳定综述。建议扩大来源或调整切入点。`
  - 是否可重试：是
- 错误类型 8：结果质量不足
  - 触发条件：digest 无足够高置信内容
  - 用户提示：`今日高置信结果较少，已提供补充候选供参考。`
  - 是否可重试：否

提示原则：
- 是否暴露具体原因：暴露用户可采取行动的原因；不暴露内部实现细节。
- 是否需要引导动作：需要，必须给出下一步建议（初始化、补配置、收集、扩大来源、调整 query）。
- 是否记录日志/审计：需要，但本文不定义内部实现方式。

---

## 13. 验收标准（Acceptance Criteria）
> 建议尽量写成 Given / When / Then。

### AC-01 初始化成功
- Given：用户首次使用 Paper Agent，选择了 `RAG` 研究方向模板，并填写了关键词 `retrieval planning, reranker` 与来源 `cs.IR, cs.AI`
- When：用户完成最小配置并执行首次运行
- Then：系统生成一份可读 digest，且用户无需修改代码

### AC-02 Digest 为默认入口
- Given：用户已完成初始化且系统已有当天新收集论文
- When：用户查看当日 digest
- Then：digest 中包含统计摘要、推荐理由、基础元数据，并可作为默认 daily intake 使用

### AC-03 Digest 高低分区
- Given：当天共筛出 18 篇论文，其中 11 篇为高置信、7 篇为低置信补充候选
- When：系统生成 digest
- Then：digest 先展示 11 篇高置信论文，再单独展示 7 篇低置信补充结果

### AC-04 Query 支持结构化回答
- Given：用户输入问题 `RAG 中的 retrieval planning 有哪些方法？`
- When：系统执行 query
- Then：系统返回结构化回答，并附支撑论文，而不是只返回无组织论文列表

### AC-05 Query 支持 Topic 聚类
- Given：用户输入 topic `vision transformer`
- When：系统执行 topic-oriented query
- Then：系统返回按 subtopic 组织的结果集合

### AC-06 Paper Detail 内容完整
- Given：用户从 digest 中选择论文 `Scaling Test-Time Compute for LLM Reasoning`
- When：系统返回 paper detail
- Then：结果包含核心元数据、推荐解释、关联上下文和可导出信息

### AC-07 Topic Report 是独立产物
- Given：用户请求 topic `retrieval-augmented generation`
- When：系统生成 topic report
- Then：结果以独立 artifact 存在，可被再次查看和 agent 消费

### AC-08 Agent 可消费四类对象
- Given：agent 通过 CLI 请求 digest、query result、paper detail、topic report
- When：系统分别返回结果
- Then：四类对象均以稳定结构化方式输出，且可被后续串联使用

### AC-09 方法相似性检索返回方法维度结果
- Given：本地库中包含多篇使用 MCTS 做 reasoning planning 的论文以及使用其他方法的论文
- When：用户提供方法描述 `Monte Carlo Tree Search for test-time reasoning`
- Then：系统返回的结果优先包含使用 MCTS 或 tree search 类方法的论文，而非仅按 "reasoning" topic 匹配

### AC-10 目标相似性检索返回跨方法结果
- Given：本地库中包含多篇解决 RAG hallucination 问题的论文，分别使用 reranking、self-reflection、citation grounding 等不同方法
- When：用户输入目标 `减少 RAG 系统中的幻觉问题`
- Then：系统返回所有试图解决该目标的论文，不限于某一种方法路径

### AC-11 综述结构完整性
- Given：本地库中包含 30+ 篇关于 retrieval-augmented generation 的论文
- When：用户请求生成综述，切入点为 `retrieval-augmented generation`
- Then：综述至少包含问题定义、方法分类学（按 subtopic 或技术路径分类）、方法对比分析、研究空白识别、未来方向建议

### AC-12 综述是独立 artifact
- Given：用户已生成一篇综述
- When：agent 通过 CLI 请求该综述
- Then：综述以稳定结构化对象返回，可被再次查看和 agent 消费

### AC-13 未初始化错误恢复
- Given：新用户尚未初始化
- When：用户直接请求 digest
- Then：系统不执行 digest，提示先初始化，并允许用户返回初始化流程

### AC-14 空库查询恢复
- Given：用户已初始化，但本地库为空
- When：用户执行 query `test-time scaling`
- Then：系统返回空结果提示，并引导用户先执行收集或检查来源配置

---

## 14. 埋点 / 日志 / 审计要求
> 按需填写。

### 埋点
- 事件 1：初始化完成并产出首份 digest
- 事件 2：用户查看 digest
- 事件 3：用户从 digest 跳转到 paper detail / search / inbox
- 事件 4：用户发起 query
- 事件 5：用户生成 topic report
- 事件 6：agent 请求五类对象
- 事件 7：用户发起方法相似性检索
- 事件 8：用户发起目标相似性检索
- 事件 9：用户生成综述

### 日志
- 记录内容：功能入口、结果类型、成功/失败状态、错误类别、恢复引导动作
- 记录时机：初始化完成、digest 生成、query 完成、report 生成、异常发生时

### 审计
- 审计动作：生成 digest、生成 topic report、生成 survey、agent 调用关键对象
- 审计字段：调用时间、对象类型、结果状态、触发来源（用户 / agent）

---

## 15. 兼容性要求
> 如果涉及旧逻辑，明确兼容方式。

填写：
- 与旧功能关系：v01 当前无历史正式版本兼容包袱。
- 老用户影响：无。
- 老数据影响：[待确认] 若后续存在旧版 digest / report，是否需要统一对象定义。
- 多端/多版本差异：v01 仅定义 CLI-first 行为，不定义多端差异。

---

## 16. 未决问题
### P0
- 问题 1：[待确认] topic report 在数据不足时是否允许降级生成轻量版 report？
- 问题 2：[待确认] 来源模板与研究方向模板同时选择时，默认冲突解决规则是什么？

### P1
- 问题 1：[待确认] 辅助 inbox 是否需要支持多个队列或仅单一待处理列表？
- 问题 2：[待确认] 是否需要为不同 query mode 明确定义默认输出优先级（retrieval / structured QA / clustering）？

---

## 17. 附件
- Requirement Doc：[Requirement Doc](./requirement.md)
- 原型图：无
- 流程图：无
- 文案清单：见本文错误提示与验收标准

---

# 18. 【BDD 场景集】

```gherkin
Feature: Initialize Paper Agent with templates and minimal configuration

  Scenario: First-time user initializes with a research-direction template and gets the first digest
    Given Lin is using Paper Agent for the first time
    And Lin selects the "RAG" template
    And Lin fills topics with "retrieval-augmented generation"
    And Lin fills keywords with "retrieval planning, reranker"
    And Lin selects sources "cs.IR" and "cs.AI"
    And Lin selects provider "Anthropic"
    When Lin completes initialization and runs the first workflow
    Then Paper Agent returns a readable digest
    And the digest contains recommended papers and summary statistics

  Scenario: User initializes with a source template and later refines preferences
    Given Mei selects the source template "arXiv-cs.AI + arXiv-cs.CL"
    And Mei fills topics with "LLM agents"
    And Mei fills keywords with "tool use, planning"
    When Mei runs the first workflow
    Then Paper Agent returns a digest for the selected sources
    And Mei can refine the configuration afterward
```

```gherkin
Feature: Digest-first daily intake

  Scenario: User reads a digest with high-confidence and supplemental sections
    Given today's collection produced 18 candidate papers
    And 11 papers are classified as high-confidence
    And 7 papers are classified as supplemental candidates
    When Jun opens the digest for 2026-03-10
    Then the digest first shows the 11 high-confidence papers
    And then shows the 7 supplemental papers in a separate section
    And the digest includes title, authors, abstract, source, link, relevance score, recommendation reason, and summary statistics

  Scenario: User opens paper detail from digest
    Given Yun is reading the digest for 2026-03-10
    And the digest contains the paper "Scaling Test-Time Compute for LLM Reasoning"
    When Yun selects that paper
    Then Paper Agent returns the paper detail
    And the detail includes recommendation explanation and related context

  Scenario: User continues search after reading digest
    Given Hao reads a digest containing papers about "retrieval planning"
    When Hao starts a new query for "test-time planning in RAG"
    Then Paper Agent returns query results built on top of search

  Scenario: User sends a digest result to auxiliary inbox
    Given Qian reads a digest and finds "Hierarchical Retrieval Planning for Long-Context QA"
    When Qian marks it for later processing
    Then the paper is added to the auxiliary inbox or reading queue

  Scenario: User hands digest results to an agent
    Given Rui reads a digest containing 12 high-confidence papers
    When Rui asks an automation agent to continue from today's digest
    Then the agent can consume the digest as a structured object
```

```gherkin
Feature: Query and structured answer generation

  Scenario: User asks a research question and receives a structured answer
    Given the local paper library contains papers about retrieval planning, reranking, and iterative search
    When Wei asks "RAG 中的 retrieval planning 有哪些方法？"
    Then Paper Agent returns a structured answer
    And the answer includes supporting papers

  Scenario: User requests topic-oriented clustering
    Given the local paper library contains 46 papers related to vision transformers
    When Nan queries "vision transformer"
    Then Paper Agent returns results grouped by subtopics
    And at least one subtopic contains representative papers

  Scenario: User only needs retrieval results
    Given the local paper library contains papers on test-time scaling
    When Bo queries "test-time scaling"
    Then Paper Agent may return ranked retrieval results
    And the results can be reused for later synthesis

  Scenario: Agent performs context-aware retrieval from a code task
    Given an agent is working on a file about reranking and retrieval planning
    And the task description is "improve RAG retrieval strategy"
    When the agent requests context-aware retrieval
    Then Paper Agent returns research results relevant to reranking and retrieval planning
```

```gherkin
Feature: Topic report generation

  Scenario: User generates a medium-depth topic report
    Given the local paper library contains 63 papers about retrieval-augmented generation
    When Li requests a topic report for "retrieval-augmented generation"
    Then Paper Agent returns a medium-depth topic report
    And the report is organized by subtopics
    And the report can be saved and reused later

  Scenario: Agent consumes a topic report artifact
    Given a topic report for "vision transformer" already exists
    When an agent requests that topic report
    Then Paper Agent returns the topic report as a structured object
```

```gherkin
Feature: Method-similarity paper discovery

  Scenario: User finds method-similar papers from a paper ID
    Given the local paper library contains papers about MCTS-based reasoning, beam search reasoning, and greedy decoding
    And the paper "Test-Time Planning with MCTS for LLM Reasoning" exists in the library
    When Yun requests method-similar papers for that paper
    Then Paper Agent returns papers that use MCTS or tree-search-based methods
    And the results are ranked by method similarity rather than topic overlap

  Scenario: User finds method-similar papers from a text description
    Given the local paper library contains papers using various techniques
    When Bo describes the method as "contrastive learning with hard negative mining for dense retrieval"
    Then Paper Agent returns papers that use contrastive learning or hard negative mining techniques
    And the results include papers across different application domains that share the same method

  Scenario: Method extraction fails for vague input
    Given a user provides the description "a good method for NLP"
    When Paper Agent attempts to extract method features
    Then Paper Agent returns an error indicating insufficient method detail
    And suggests providing more specific technique or algorithm names
```

```gherkin
Feature: Objective-based paper discovery

  Scenario: User finds papers by research objective
    Given the local paper library contains papers addressing RAG hallucination using reranking, self-reflection, and citation grounding
    When Wei describes the objective as "减少 RAG 系统中的幻觉问题"
    Then Paper Agent returns papers across all three method families
    And results are ranked by objective relevance, not method similarity

  Scenario: User combines objective search with method clustering
    Given the local paper library contains 40 papers about improving code generation accuracy
    When Hao searches by objective "improve code generation correctness" and requests method clustering
    Then Paper Agent returns results grouped by method approach (e.g., test-driven generation, self-repair, formal verification)
```

```gherkin
Feature: Literature survey generation

  Scenario: User generates a survey from a topic
    Given the local paper library contains 35 papers about retrieval-augmented generation
    When Li requests a survey for "retrieval-augmented generation"
    Then Paper Agent returns a structured survey artifact
    And the survey includes problem definition, method taxonomy, comparative analysis, research gaps, and future directions
    And the survey can be saved and reused later

  Scenario: User generates a survey from a research objective
    Given the local paper library contains 25 papers addressing test-time compute scaling for LLM reasoning
    When Qian requests a survey with objective "scaling test-time compute for better reasoning"
    Then Paper Agent returns a survey organized by different scaling approaches
    And the survey includes comparative analysis across methods

  Scenario: Survey generation fails due to insufficient data
    Given the local paper library contains only 3 papers about "quantum-inspired optimization for chip placement"
    When Fang requests a survey for that topic
    Then Paper Agent does not generate a formal survey
    And shows "当前相关论文不足，无法生成稳定综述。建议扩大来源或调整切入点。"

  Scenario: Agent consumes a survey artifact
    Given a survey for "vision transformer" already exists
    When an agent requests that survey
    Then Paper Agent returns the survey as a structured object
```

```gherkin
Feature: Error and recovery flows

  Scenario: User requests digest before initialization
    Given Chen has not completed initialization
    When Chen requests today's digest
    Then Paper Agent does not generate a digest
    And shows "尚未完成初始化。请先执行初始化流程。"

  Scenario: User queries an empty library
    Given Ming has completed initialization
    And Ming's local paper library is empty
    When Ming searches for "test-time scaling"
    Then Paper Agent returns no results
    And shows "当前本地论文库为空。请先执行收集，或检查来源配置。"

  Scenario: User requests a topic report with insufficient data
    Given the local paper library contains only 2 papers about "adaptive RAG planning"
    When Fang requests a topic report for "adaptive RAG planning"
    Then Paper Agent does not generate a formal topic report
    And shows "当前主题相关论文不足，暂无法生成稳定 Topic Report。建议扩大来源或调整查询。"

  Scenario: Agent request is missing required input
    Given an automation agent sends a request without query and without context
    When Paper Agent receives the request
    Then Paper Agent returns a structured error result
    And shows "请求缺少必要输入，无法生成结果。"
```

---

# 19. 【决策表】

## 决策表 1：Digest 展示分区规则

| 条件 / 规则 | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|
| 已完成初始化 | Y | Y | Y | Y | N |
| 当日有候选论文 | Y | Y | Y | N | - |
| 高置信论文数量 > 0 | Y | Y | N | - | - |
| 低置信补充论文数量 > 0 | Y | N | Y | - | - |
| 动作：展示高置信区 | Y | Y | N | N | N |
| 动作：展示低置信补充区 | Y | N | Y | N | N |
| 动作：提示“今日高置信较少” | N | N | Y | N | N |
| 动作：提示“无候选论文” | N | N | N | Y | N |
| 动作：提示“请先初始化” | N | N | N | N | Y |

说明：
- R1：有高置信也有低置信 → 两区都展示。
- R2：只有高置信 → 仅展示高置信区。
- R3：没有高置信但有低置信 → 展示低置信补充区并提示质量不足。
- R4：无候选论文 → 返回空 digest 提示。
- R5：未初始化 → 阻止 digest 生成。

## 决策表 2：Query 输出模式规则

| 条件 / 规则 | R1 | R2 | R3 | R4 | R5 | R6 | R7 |
|---|---|---|---|---|---|---|---|
| 本地库中有相关结果 | Y | Y | Y | Y | Y | Y | N |
| 输入是研究问题 | Y | N | N | N | N | N | - |
| 输入是 topic 探索 | N | Y | N | N | N | N | - |
| 输入带文件/代码/任务上下文 | N | N | Y | N | N | N | - |
| 输入是方法描述 | N | N | N | Y | N | N | - |
| 输入是目标描述 | N | N | N | N | Y | N | - |
| 用户只需基础检索 | N | N | N | N | N | Y | - |
| 输出：结构化回答 | Y | N | N | N | N | N | N |
| 输出：按 subtopic 聚类 | N | Y | N | N | N | N | N |
| 输出：上下文检索结果 | N | N | Y | N | N | N | N |
| 输出：方法相似性结果 | N | N | N | Y | N | N | N |
| 输出：目标相关性结果 | N | N | N | N | Y | N | N |
| 输出：基础 retrieval result | N | N | N | N | N | Y | N |
| 输出：空结果 / 恢复引导 | N | N | N | N | N | N | Y |

说明：
- R1：问题型 query → 输出结构化回答。
- R2：topic 型 query → 输出聚类结果。
- R3：上下文型 query → 输出上下文检索结果。
- R4：方法描述型 query → 输出方法相似性结果。
- R5：目标描述型 query → 输出目标相关性结果。
- R6：基础检索型 query → 输出 retrieval results。
- R7：无相关结果 → 返回空结果与引导。

## 决策表 3：Topic Report 生成规则

| 条件 / 规则 | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| 已完成初始化 | Y | Y | Y | N |
| 本地库中有 topic 相关结果 | Y | Y | N | - |
| 相关结果数量足以支撑正式 report | Y | N | N | - |
| 用户明确请求 topic report | Y | Y | Y | Y |
| 输出：正式 topic report artifact | Y | N | N | N |
| 输出：仅返回 topic clustering / 检索结果 | N | Y | N | N |
| 输出：提示“结果不足，建议扩大来源” | N | Y | Y | N |
| 输出：提示“请先初始化” | N | N | N | Y |

说明：
- R1：满足条件 → 生成正式 report。
- R2：有相关结果但不足以形成正式 report → 返回聚类/检索结果并提示不足。
- R3：无相关结果 → 返回失败引导。
- R4：未初始化 → 阻止执行。

## 决策表 4：方法/目标相似性检索规则

| 条件 / 规则 | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|
| 已完成初始化 | Y | Y | Y | Y | N |
| 输入提供了论文 ID 或方法描述 | Y | N | N | N | - |
| 输入提供了目标描述 | N | Y | N | N | - |
| 输入同时提供方法与目标 | N | N | Y | N | - |
| 无有效输入 | N | N | N | Y | - |
| 输出：方法相似性结果 | Y | N | Y | N | N |
| 输出：目标相关性结果 | N | Y | Y | N | N |
| 输出：组合交叉结果 | N | N | Y | N | N |
| 输出：输入不足提示 | N | N | N | Y | N |
| 输出：提示"请先初始化" | N | N | N | N | Y |

说明：
- R1：仅方法输入 → 返回方法相似性结果。
- R2：仅目标输入 → 返回目标相关性结果。
- R3：同时提供方法与目标 → 返回交叉组合结果。
- R4：无有效输入 → 返回提示。
- R5：未初始化 → 阻止执行。

## 决策表 5：综述生成规则

| 条件 / 规则 | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| 已完成初始化 | Y | Y | Y | N |
| 本地库中有相关结果 | Y | Y | N | - |
| 相关结果数量与方法多样性足以支撑综述 | Y | N | N | - |
| 用户明确请求综述 | Y | Y | Y | Y |
| 输出：正式综述 artifact | Y | N | N | N |
| 输出：仅返回检索/聚类结果 | N | Y | N | N |
| 输出：提示"结果不足，建议扩大来源" | N | Y | Y | N |
| 输出：提示"请先初始化" | N | N | N | Y |

说明：
- R1：满足条件 → 生成正式综述。
- R2：有相关结果但不足以形成综述 → 返回聚类结果并提示不足。
- R3：无相关结果 → 返回失败引导。
- R4：未初始化 → 阻止执行。

---

# 20. 【错误恢复旅程】

| 错误类型 | 用户看到什么 | 系统引导 | 回到正轨 |
|---|---|---|---|
| 未初始化 | `尚未完成初始化。请先执行初始化流程。` | 引导用户进入初始化，选择模板并补齐最小配置 | 完成初始化并生成首份 digest |
| 配置不完整 | `当前配置不完整，请补齐必要配置后重试。` | 列出缺失配置项，如 topics、sources、provider | 补齐配置后重新执行 digest / query / report |
| 本地库为空 | `当前本地论文库为空。请先执行收集，或检查来源配置。` | 引导先执行 collection 或修正来源模板/来源配置 | 完成收集后重新执行 search / digest / report |
| Topic 数据不足 | `当前主题相关论文不足，暂无法生成稳定 Topic Report。建议扩大来源或调整查询。` | 引导扩大来源、放宽 topic、先执行 query clustering | 通过扩大数据范围后重新生成 topic report |
| Agent 输入不完整 | `请求缺少必要输入，无法生成结果。` | 提示补充 query、对象类型或上下文 | agent 补全输入后重试 |
| Digest 质量不足 | `今日高置信结果较少，已提供补充候选供参考。` | 引导用户查看低置信补充区，或后续调整兴趣/来源配置 | 用户先消费可用结果，之后优化配置 |
| 方法提取失败 | `无法从输入中提取有效方法特征。请提供更具体的方法或技术描述。` | 引导用户提供更具体的 technique、algorithm 或 framework 描述 | 用户提供更具体的方法描述后重试 |
| 综述数据不足 | `当前相关论文不足，无法生成稳定综述。建议扩大来源或调整切入点。` | 引导扩大来源、调整切入点、先执行方法/目标检索 | 通过扩大数据范围后重新生成综述 |
| 数据不存在 | `未找到对应论文或可用主题结果。` | 引导用户重新选择论文、调整 query 或扩大来源 | 用户改用可命中的 paper / query 重试 |

---

**Next Steps:** 基于本 Functional Spec，对 [Requirement Doc](./requirement.md) 中的 FR / BR / NFR 做逐条映射，补齐 `docs/v01/mvp.md` 中 Must/Should 的范围收敛。
