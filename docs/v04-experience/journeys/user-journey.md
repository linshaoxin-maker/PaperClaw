# Paper Agent v04-experience — 用户旅程

**Phase:** Phase 0
**Last Updated:** 2026-03-16
**Baseline:** `../../v02/journeys/user-journey.md`

---

## 旅程总览

v04-experience 不新增旅程阶段，而是 **深化** 已有旅程的每个触点，让研究者在同样的交互中获得更深、更准、更快的结果。

v04 新增 **Obsidian 知识库联动**：所有输出件自动同步到 Obsidian vault，用户在 Obsidian 中浏览论文、查看知识图谱、使用 Dataview 动态查询。

---

## 旅程 0：初始化 & Obsidian 联动（新增）

### 触点 0.1：首次设置

| 步骤 | 操作 | 结果 |
|------|------|------|
| 1 | `paper-agent init` | 创建 `.paper-agent/` 目录（项目本地） |
| 2 | 用 Obsidian 打开 `.paper-agent/` 作为 vault | 看到完整目录结构 |
| 3 | 安装 Dataview + Calendar 插件 | Dashboard 和查询页生效 |

初始化后自动生成：
- `00-Dashboard.md` — Dataview 动态仪表盘
- `02-论文库/` 下 6 个预置查询页（高分论文、按方法/年份/会议分类、阅读进度、最近入库）
- `.obsidian/` 配置（wikilink 模式、Graph View 颜色分组、书签）

### 触点 0.2：同步论文库到 Obsidian

| 项 | 说明 |
|----|------|
| 触发方式 | 对 Claude 说"同步论文到 Obsidian" |
| 工具调用 | `paper_sync_vault(limit=0)` |
| 结果 | 数据库中所有论文生成为 Obsidian markdown 文件到 `02-论文库/` |
| 论文卡片内容 | YAML frontmatter + 层级标签 + 引用 wikilink + Method Profile + Notes |
| 增量同步 | 已存在的不覆盖，只同步新论文 |

---

## 旅程 1：每日论文 Intake

### 触点 1.1：晨报 (Morning Brief)

| 项 | v03 行为 | v04-experience 行为 |
|----|---------|-------------------|
| 触发方式 | `/start-my-day` → Skill 编排 3 步（context → collect → digest） | `/start-my-day` → Skill 直接调用 `paper_morning_brief`（1 步） |
| 返回内容 | title + score + abstract（信息密度低） | title + score + abstract + **methodology_tags + citation_count + venue + credibility_hint** |
| watchlist 更新 | 无 | morning_brief 后自动调用 `paper_watch_check`，追加"关注领域更新"板块 |
| Obsidian 联动 | 无 | **报告自动保存到 `01-每日推荐/`，涉及的论文自动同步到 `02-论文库/`，wikilink 互相链接** |
| 用户感受 | 😐 信息不够做判断，需要逐篇追问 | 😊 一眼看出论文重要性，Obsidian 里点击直达论文卡片 |

**关键改进**：
- `_format_paper()` 在 Digest markdown 中增加信息字段
- Skill 新增步骤：morning_brief 完成后调用 `paper_watch_check`

### 触点 1.2：论文筛选

| 项 | v03 行为 | v04-experience 行为 |
|----|---------|-------------------|
| scoring 方式 | LLM 逐篇串行评分 | **Batch scoring**（5-8 篇/批）+ **title 预过滤** |
| 200 篇耗时 | ~5 分钟 | ~2 分钟 |
| 反馈效果 | 记录但不影响推荐 | **偏好分值偏移**影响下次 scoring |
| 用户感受 | 😟 等太久 | 😊 快了不少 |

**关键改进**：
- FilteringManager 支持 batch prompt
- 预过滤逻辑：title 中不含 profile topics/keywords 任何近义词的论文降低优先级或直接标记 low
- 读取 `paper_preferences()` 中的 topic 偏好调整 base score

### 触点 1.3：下载 PDF

| 项 | v03 行为 | v04-experience 行为 |
|----|---------|-------------------|
| arXiv 论文 | ✅ 正常下载 | ✅ 不变 |
| 非 arXiv 论文 | ❌ skip | **fallback**: S2 openAccessPdf → DOI resolver → 报告 "无免费全文" |
| 下载成功率 | ~50% | ~75-80% |
| 用户感受 | 😡 一半论文下不了 | 😊 大部分能下 |

**关键改进**：
- `paper_download` 工具增加 fallback 链

---

## 旅程 2：深度研究

### 触点 2.1：单篇深入分析

| 项 | v03 行为 | v04-experience 行为 |
|----|---------|-------------------|
| 分析基础 | 只看 abstract + metadata | **自动检测 PDF 可用性** → 有 PDF: `paper_parse` → `paper_extract` → 基于全文分析 |
| 可信度评估 | 不可用（用户不知道） | Skill 自动调用 `paper_credibility` |
| Paper Q&A | 不可用（用户不知道） | Skill 提示"你可以对这篇论文提问"，引导使用 `paper_ask` |
| 输出报告标注 | 无标注 | 标注 "[基于全文]" 或 "[基于摘要]" |
| 用户感受 | 😟 分析浅薄 | 😃 真的读了论文 |

**关键改进**：
- Insight Skill 新增 Phase: "Deep-dive" —— 条件分支：
  ```
  IF 论文已有 PaperProfile → 直接使用
  ELIF 论文有 PDF → paper_parse → paper_extract → 使用提取结果
  ELSE → 基于 abstract + metadata 做浅层分析（标注 [基于摘要]）
  ```
- Insight Skill 新增 Phase: "可信度评估" —— 自动调用 `paper_credibility`
- Insight Skill 新增 Phase: "Q&A 引导" —— 提示用户可以追问

### 触点 2.2：多篇对比

| 项 | v03 行为 | v04-experience 行为 |
|----|---------|-------------------|
| 对比数据 | `paper_compare` 搬运 metadata（methodology_tags 大多为空） | 自动检测每篇论文是否有 Profile，无则调用 `paper_extract`，再调用 `paper_compare_table` |
| 对比维度 | title, authors, score, abstract | **task, method_family, datasets, baselines, metrics, limitations** |
| 输出格式 | AI 自由组织 | 结构化对比表 + AI 叙述分析 |
| 用户感受 | 😟 对比表信息太少 | 😃 一目了然 |

**关键改进**：
- Compare Skill 新增自动 extract 步骤
- Skill 优先使用 `paper_compare_table`（返回结构化 JSON），AI 负责在此基础上做洞察叙述

### 触点 2.3：文献综述

| 项 | v03 行为 | v04-experience 行为 |
|----|---------|-------------------|
| 趋势分析 | AI 基于 abstract 猜测 | `paper_trend_data` 提供年度/月度论文分布统计 |
| 方法分类 | AI 推断 | `paper_field_stats` 提供方法/数据集/任务分布统计 |
| 综述数据支撑 | 0% 硬数据 | 关键统计字段由工具数据预填充，AI 基于硬数据写叙述 |
| 用户感受 | 😐 综述看着不可靠 | 😊 有数据支撑 |

**关键改进**：
- Survey/Insight Skill 在生成报告前调用 `paper_trend_data` 和 `paper_field_stats`
- 模板中标注数据来源：`[数据来源: paper_trend_data]`

---

## 旅程 3：能力发现与个性化

### 触点 3.1：功能发现

| 项 | v03 行为 | v04-experience 行为 |
|----|---------|-------------------|
| 意图覆盖 | router 支持 ~8 个意图 | router 支持 ~20 个意图（覆盖所有 v03-v06 工具） |
| 高级功能引导 | 无 | "有什么 idea?" → paper_ideate; "可信吗?" → paper_credibility |
| 用户感受 | 😐 不知道还能做什么 | 😃 随口说就能用 |

**关键改进**：
- Router Skill / paper-router.md 新增意图映射表

### 触点 3.2：偏好反馈

| 项 | v03 行为 | v04-experience 行为 |
|----|---------|-------------------|
| 反馈记录 | ✅ paper_feedback 记录到 DB | ✅ 不变 |
| 反馈效果 | ❌ 记录但不影响推荐 | ✅ 偏好读取 → scoring 权重调整 → 推荐排序变化 |
| 偏好可见 | ❌ 不可查看 | ✅ `paper_preferences` 展示学到的偏好总结 |
| 用户感受 | 😟 反馈无效果 | 😊 系统在学习 |

---

## 错误恢复旅程

| 错误场景 | 用户看到的 | 系统引导 | 回正轨 |
|---------|----------|---------|-------|
| PDF 解析失败 | "PDF 解析遇到问题" | "将基于摘要进行分析 [基于摘要]" | 自动降级到 abstract-based 分析 |
| Batch scoring 部分论文评分为空 | "以下 N 篇论文评分异常" | "正在逐篇重新评分..." | 自动 fallback 到逐篇 scoring |
| S2 PDF URL 失效 | "S2 链接无法访问" | "尝试通过 DOI 获取..." | 自动 fallback 到 DOI resolver |
| paper_extract 提取结果不完整 | "部分字段提取置信度较低 [低置信度]" | "建议查看论文原文确认" | 标注低置信度字段，不阻断流程 |
| Watchlist 无更新 | "您关注的领域最近无新论文" | "上次更新: X 天前" | 展示最后一次更新时间，不报错 |
| Feedback 偏好冲突（同 topic 既标高又标低） | "检测到偏好冲突" | "最近 3 次反馈倾向: [方向]，是否更新？" | 用最近反馈覆盖旧反馈 |

---

## v05 新增旅程改进

**Last Updated:** 2026-03-15

v05 在 v04 基础上进一步深化，核心改变：**每个交互触点结束后，系统主动预测下一步并推荐操作。**

### 改进 1：Context-Aware Next-Step Prediction

| 项 | v04 行为 | v05 行为 |
|----|---------|---------|
| Skill 结束后 | 静态 FORK："深入看哪篇？还是先这样？" | **基于结果数据的智能推荐**："筛出 3 篇重要论文。要批量下载 PDF？还是先深入看 [DREAMPlace v4]（9.2分）？" |
| 推荐内容 | 固定 2-3 个选项，跟上下文无关 | 引用实际论文标题、分数、数量，最多 3 个选项 |
| 上下文传递 | 用户需要重新描述意图 | paper IDs、scores、topics 自动传递到下一步 |
| 退出方式 | 每次都问"还是先这样？" | 退出是隐式的——用户不说话就是结束 |

### 改进 2：信息密度提升

| 触点 | v04 输出 | v05 输出 |
|------|---------|---------|
| 搜索结果 | title + score + source | title + score + **abstract_snippet(400字) + authors(5人) + venue + citation_count + doi + pdf_url + methodology_tags** |
| Triage 结果 | id + title + score + reason | + **abstract_snippet + authors + url + topics + methodology_tags + venue + citation_count + pdf_url** |
| Digest markdown | authors(3人) + abstract(300字) | **authors(5人) + abstract(500字) + PDF/DOI 链接 + citation_count + venue tier emoji** |
| BibTeX 导出 | 全部 @article，无 doi | **@inproceedings vs @article 自动判断 + AuthorYear cite_key + doi + booktitle/journal** |

### 改进 3：PaperProfile 结构化提取增强

| 字段 | v04 | v05 |
|------|-----|-----|
| novelty_claim | ❌ 无 | ✅ 一句话新颖性声明 |
| problem_formulation | ❌ 无 | ✅ 问题建模方式（如"placement as RL"） |
| key_contributions | ❌ 无 | ✅ 2-4 条核心贡献 |
| 对比表格 | task + method + datasets | + **novelty + problem** 列 |

### 改进 4：Feedback Loop 闭环

| 组件 | v04 | v05 |
|------|-----|-----|
| FilteringManager | ✅ 已集成 feedback offset | ✅ 不变 |
| SearchEngine._rerank() | ❌ 不受 feedback 影响 | ✅ **topic preference weights 影响排序** |
| DigestGenerator | ❌ 不受 feedback 影响 | ✅ **feedback-adjusted scores 影响推荐顺序** |

### 改进 5：Venue 分类修复

| 问题 | v04 | v05 |
|------|-----|-----|
| "date" 误匹配 | ❌ "updated" 被识别为 DATE 会议 | ✅ **word-boundary regex 精确匹配** |
| "www" 误匹配 | ❌ URL 中的 www 被识别为 WWW 会议 | ✅ **\bwww\b 只匹配独立词** |
| EDA 期刊缺失 | ❌ TODAES/TCAS/TVLSI 未收录 | ✅ **补充 5 个 EDA 期刊** |
| ICLR Workshop | ❌ 被识别为 top venue | ✅ **workshop 检测优先于 top venue** |

### 改进 6：Source Adapter 数据丰富度

| 数据源 | v04 新增字段 | v05 新增字段 |
|--------|------------|------------|
| arXiv | doi, pdf_url | + **venue(from journal_ref), all_categories, comment, updated_at** |
| Semantic Scholar | TLDR, influentialCitationCount | ✅ 不变 |
| OpenReview | decision, TLDR | ✅ 不变 |
| OpenAlex | affiliations | ✅ 不变 |
| DBLP | — | + **doi** |

---

## 旅程 5：Obsidian 知识库浏览（新增）

### 触点 5.1：打开 Obsidian 浏览知识库

| 步骤 | 用户操作 | 看到什么 |
|------|---------|---------|
| 1 | 打开 Obsidian vault | 左侧目录：00-Dashboard、01-每日推荐、02-论文库... |
| 2 | 点 `00-Dashboard.md` | Dataview 动态仪表盘：论文统计、高分论文、最近推荐、综述列表 |
| 3 | 点 `02-论文库/_高分论文.md` | 自动列出 score ≥ 8 的论文表格 |
| 4 | 点任意论文卡片 | 完整信息：frontmatter + 标签 + 摘要 + Method Profile + 引用链接 |
| 5 | 点 Graph View (`Cmd+G`) | 论文关联网络图谱，颜色区分不同目录 |
| 6 | 点 Calendar 视图 | 按日期浏览每日推荐时间线 |

### 触点 5.2：Obsidian 内搜索和筛选

| 方式 | 说明 |
|------|------|
| 全文搜索 | `Cmd+Shift+F` 搜索所有论文和笔记 |
| 标签筛选 | 点击 `#method/GNN` 等标签，查看同类论文 |
| Dataview 查询 | `_按方法分类.md`、`_按会议分类.md`、`_按年份分布.md` |
| Graph View 过滤 | 在图谱中按路径/标签过滤，聚焦特定研究方向 |

### 触点 5.3：Claude 输出 → Obsidian 实时更新

| Claude 操作 | Obsidian 中的变化 |
|-------------|-----------------|
| `start my day` | `01-每日推荐/` 出现今日推荐，涉及论文同步到 `02-论文库/` |
| 分析一篇论文 | `03-深度分析/` 出现分析笔记，论文卡片同步 |
| 写综述 | `05-文献综述/` 出现综述报告，所有引用论文同步 |
| 对比论文 | `04-对比分析/` 出现对比报告 |
| 引用追踪 | `10-引用追踪/` 出现追踪图，Graph View 自动更新关联 |

**用户无需任何额外操作**，所有同步由 `paper_save_report(paper_ids=...)` 自动完成。
