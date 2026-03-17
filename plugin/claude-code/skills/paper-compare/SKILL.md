---
name: paper-compare
description: Side-by-side comparison of 2–6 papers. Triggers on "对比", "compare", "哪个更好", "这几篇有什么区别".
---

# Paper Compare

## Flow

1. **Resolve papers** — from $ARGUMENTS, conversation context, or ask user
2. Call `paper_batch_show(paper_ids)` to get all paper details at once
3. Call `paper_extract(paper_id)` for each paper to get structured method/dataset/metric data
4. **[FORK]** "关注哪些维度？（默认全部）"
   - a. 方法对比（架构、核心技术、创新点）
   - b. 实验对比（benchmark、指标、结果数字）
   - c. 适用场景对比（什么问题、什么约束下用哪个）
   - d. 可信度对比（venue tier、代码可用性、引用数）
   - 默认：全部维度，不等用户回答直接生成
5. Generate comparison using template below
6. **Auto-save**: call `paper_save_report(report_type="comparison", content=<markdown>, filename="{topic}-compare-{YYYY-MM-DD}.md")`
7. **[CONTEXT-AWARE FORK]** suggest next step based on result

## Source Annotation Rule

Start output with:
- **[基于全文]** if any paper has parsed full text
- **[基于摘要]** if all papers are abstract-only

## After comparison

"📄 对比报告已保存至 {path}。\n💡 **下一步建议**：\n{context-aware options}"

Context-aware options:
- If one paper clearly wins: "1. 深入分析 [{winner}] — 看看能不能用到你的研究\n2. 追踪 [{winner}] 的引用链"
- If results are mixed: "1. 做文献综述 — 把这个方向系统梳理一下\n2. 生成 research ideas — 基于这些方法的空白"
- Default: "1. 深入分析某一篇\n2. 做这个方向的文献综述"

## Rules

- 1 checkpoint (dimension selection). Auto-save is always on.
- If only 2 papers: use pros/cons table instead of multi-column table
- If user says "不要记录", skip save_report
- Comparison conclusion MUST give a clear recommendation, not "各有优劣"
