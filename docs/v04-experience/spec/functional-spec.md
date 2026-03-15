# Paper Agent v04-experience — Functional Spec

**Phase:** Phase 2 (功能规格)
**Last Updated:** 2026-03-15

---

## FS-01: Paper 序列化补全

### 触发方式
任何 MCP 工具调用 `paper.to_summary_dict()`, `paper.to_detail_dict()`, 或 `paper.to_compact_dict()` 时自动生效。

### 系统行为

**to_summary_dict() 新增字段**：

| 字段 | 值 | 说明 |
|------|-----|------|
| `reading_status` | `str \| null` | "to_read" / "reading" / "read" / "important" / null |
| `canonical_key` | `str` | arXiv ID 或 S2 ID，空字符串当不可用 |
| `source_paper_id` | `str` | 来源系统中的原始 ID |

**to_detail_dict() 新增字段**：

| 字段 | 值 | 说明 |
|------|-----|------|
| `reading_status` | `str \| null` | 同上 |
| `canonical_key` | `str` | 同上 |
| `source_paper_id` | `str` | 同上 |
| `created_at` | `str (ISO 8601)` | 入库时间 |
| `pdf_url` | `str \| null` | 从 metadata 中提取 |
| `doi` | `str \| null` | 从 metadata 中提取 |
| `citation_count` | `int \| null` | 从 metadata 中提取 |
| `venue` | `str \| null` | 从 metadata 中提取 |

**to_compact_dict() 新增字段**：

| 字段 | 值 |
|------|-----|
| `methodology_tags` | `list[str]` |

### 异常流程
- metadata 中无对应字段 → 返回 null，不报错

---

## FS-02: Digest 信息密度提升

### 触发方式
`DigestGenerator._format_paper()` 被调用时（digest 生成流程中）。

### 系统行为

每篇论文的 markdown 格式变为：

```markdown
### {idx}. {title}
**Score:** {score}/10 | **Source:** {source_name} | **Date:** {published_at} | **ID:** {canonical_key}
**Authors:** {authors[:3]}
**Topics:** {topics as comma-separated tags}
**Methods:** {methodology_tags as comma-separated tags}
**Why:** {recommendation_reason}
> {abstract[:300]}...
```

### 分支流程
- topics 为空 → 不展示 Topics 行
- methodology_tags 为空 → 不展示 Methods 行
- canonical_key 为空 → 不展示 ID 字段
- published_at 为空 → 不展示 Date 字段

### 异常流程
- 无异常，缺失字段静默跳过

---

## FS-03: LLM Batch Scoring

### 触发方式
`FilteringManager.filter_papers(papers, interests)` 被调用，且论文数量 > 1。

### 系统行为

**主流程**：
1. 读取配置 `batch_size`（默认 5）和 `pre_filter_enabled`（默认 True）
2. 如 `pre_filter_enabled`：执行 title 预过滤（FS-04）
3. 将待评分论文按 `batch_size` 分组
4. 对每组构建 batch prompt，一次 LLM 调用评估该组所有论文
5. 解析 LLM 返回的 JSON 数组，每个元素包含 `{paper_id, score, band, reason, topics}`
6. 如有 feedback 数据（FS-05），对每篇论文的 score 应用偏移
7. 调用 `_apply_and_persist(paper, result)` 持久化
8. 按 effective_score 降序排列返回

**LLM batch prompt 结构**：
```
System: You are a research paper relevance scorer.
User: 
Research interests: {interests}

Rate each paper's relevance (1-10 scale). Return JSON array.

Paper 1:
Title: {title}
Abstract: {abstract}

Paper 2:
...

Return format:
[
  {"paper_index": 1, "score": 8.5, "band": "high", "reason": "...", "topics": ["..."]},
  ...
]
```

### 分支流程
- 论文数量 ≤ 1 → 直接逐篇评分（不走 batch）
- batch_size 配置为 1 → 等效逐篇评分

### 异常流程
- LLM 返回非法 JSON → 该 batch 所有论文 fallback 到逐篇评分
- LLM 返回的 paper_index 不全 → 缺失论文 fallback 到逐篇评分
- ThreadPoolExecutor 异常 → 失败论文标记 score=0, reason="评分失败"

---

## FS-04: Title 预过滤

### 触发方式
`FilteringManager.filter_papers()` 中，batch scoring 前执行（当 `pre_filter_enabled=True`）。

### 系统行为

**主流程**：
1. 从 profile 获取 topics + keywords
2. 扩展同义词列表（使用 SearchEngine 的 `_SYNONYM_GROUPS`）
3. 对每篇论文：
   - 提取 `title.lower()` + `abstract[:200].lower()`
   - 检查是否包含 topics/keywords/synonyms 中任一词
4. 命中 → 标记 `needs_llm=True`
5. 未命中 → 标记 `score=1.0, band="low", reason="title pre-filtered [pre-filtered]"`, `needs_llm=False`
6. 只将 `needs_llm=True` 的论文送入 batch scoring

### 分支流程
- profile 无 topics 且无 keywords → 跳过预过滤，全部进入 LLM
- 预过滤配置关闭 → 跳过

### 异常流程
- 无异常路径

---

## FS-05: Feedback 闭环

### 触发方式
`FilteringManager.filter_papers()` 中，scoring 结果返回后，排序前。

### 系统行为

**主流程**：
1. 调用 `FeedbackManager.get_adjusted_topic_weights()` 获取 topic 偏好权重
2. 权重格式：`{"topic_name": offset_value}` （正值=用户喜欢，负值=用户不喜欢）
3. 对每篇论文：
   - 取论文 topics 与偏好 topics 的交集
   - 计算偏移量：`sum(offset for topic in intersection)` / `len(intersection)`
   - 限制偏移量范围：`clamp(offset, -2.0, +2.0)`
   - `effective_score = raw_score + offset`
   - `effective_score = clamp(effective_score, 0.0, 10.0)`
4. 按 `effective_score` 排序

### 分支流程
- 无 feedback 数据 → `get_adjusted_topic_weights()` 返回空 dict → 无偏移
- 论文无 topics → 无交集 → 无偏移

### 异常流程
- FeedbackManager 调用失败 → 降级为无偏移（log warning）

---

## FS-06: PDF 下载增强

### 触发方式
`paper_download(paper_ids, output_dir)` MCP 工具被调用。

### 系统行为

**主流程（per paper）**：
1. `_extract_arxiv_id(paper)` → 如有 arXiv ID → 构建 `https://arxiv.org/pdf/{id}.pdf` → 下载
2. 如 step 1 失败或无 arXiv ID → 检查 `paper.metadata.get("pdf_url")` → 如有 → 下载
3. 如 step 2 失败 → 检查 `paper.metadata.get("doi")` → 如有 → HEAD 请求 `https://doi.org/{doi}` → 检查 redirect 后的 Content-Type
4. Content-Type 含 "pdf" → 下载
5. Content-Type 不含 "pdf" → 返回 `{"status": "skipped", "reason": "付费文章，无免费 PDF"}`
6. 如 step 3 失败 → 返回 `{"status": "skipped", "reason": "无 arXiv ID、开放获取链接或 DOI"}`

**超时**：每步 HTTP 请求超时 30s。

### 异常流程
- 网络超时 → 返回 `{"status": "error", "reason": "网络超时"}`
- 文件写入失败 → 返回 `{"status": "error", "reason": "文件保存失败"}`

---

## FS-07: paper_find_and_download Bug 修复

### 触发方式
`paper_find_and_download(title, output_dir)` MCP 工具被调用。

### 系统行为变更

1. 修复 Paper 构建参数：`source=` → `source_name=`
2. 将 S2 返回的 `openAccessPdf.url` 存入 `Paper.metadata["pdf_url"]`
3. 持久化 Paper 到 DB 后，metadata 含 pdf_url，后续 `paper_download` 可用

---

## FS-08: Router Skill 未引用工具扩展

### 触发方式
用户通过自然语言表达意图，Router Skill 识别并路由。

### 新增意图映射

| 用户意图 | 路由到 |
|---------|-------|
| "我的偏好" / "我喜欢什么方向" / "preferences" | `paper_preferences` |
| "最近有新论文吗" / "watchlist check" | `paper_watch_check` |
| "我关注了什么" / "watchlist" | `paper_watch_list` |
| "这篇的表格" / "show tables" | `paper_tables` |
| "哪些论文用了 GNN" / "query profiles" | `paper_query` |
| "我的阅读进度" / "reading progress" | `paper_reading_stats` |
| "看看笔记" / "show notes" | `paper_note_show` |
| "工作区概览" / "workspace status" | `paper_workspace_status` |

---

## FS-09: Skill 条件分支优化

### Deep-dive Skill 标注信息来源

在分析输出中：
- 如 `paper_sections()` 返回内容 → 标注 `[基于全文]`
- 如 `paper_sections()` 返回空且无 PDF → 标注 `[基于摘要]`

### Compare workflow 自动 extract

在 `paper_compare_table` 前：
- 对每篇参与对比的论文检查是否有 PaperProfile（调用 `paper_extract` 检查缓存）
- 无 profile → 自动调用 `paper_extract(paper_id)` 提取
- 所有论文均有 profile 后 → 调用 `paper_compare_table`

### Survey workflow 数据预填充

在生成综述前：
- 调用 `paper_trend_data(topic)` 获取趋势统计
- 调用 `paper_field_stats(field="method_family")` 获取方法分布
- 将统计数据作为综述的"硬数据"基础
