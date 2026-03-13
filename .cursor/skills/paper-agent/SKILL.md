---
name: paper-agent
description: AI research paper intelligence assistant — collect, recommend, search, analyze, compare, and survey arXiv papers via MCP. Use when the user mentions paper, arxiv, digest, research, 论文, 论文分析, start my day, paper-analyze, paper-compare, paper-survey, arXiv IDs (like 2301.12345), ML method names, or asks about academic research trends.
---

# Paper Agent

Research paper intelligence powered by the paper-agent MCP server.

## MCP Tools

### Core (v01)

| Tool | Purpose | Typical Trigger |
|------|---------|-----------------|
| `paper_search` | Full-text search in local library (supports `diverse` mode for keyword expansion) | User asks about a paper, method, or technique |
| `paper_show` | Full details for a specific paper (supports bare arXiv IDs) | User wants to dive into one paper |
| `paper_collect` | Fetch from arXiv + DBLP + Semantic Scholar concurrently | User says "收集论文" or "update library" |
| `paper_digest` | Daily recommendations | User says "今日推荐" or "start my day" |
| `paper_stats` | Library statistics | User asks "库里有多少论文" |
| `paper_profile` | Research profile info | User asks "我的研究方向" |
| `paper_profile_update` | Create/update profile via conversation | User describes research interests |
| `paper_sources_list` | List all available sources | User asks about arXiv categories |
| `paper_sources_enable` | Enable/disable sources | User wants to add/remove categories |
| `paper_templates_list` | List research area templates | User wants a preset template |

### Multi-Paper Intelligence (v02)

| Tool | Purpose | Typical Trigger |
|------|---------|-----------------|
| `paper_search_batch` | Search multiple topics at once (grouped results) | User wants to survey/compare N research directions |
| `paper_batch_show` | Get papers info (compact by default, `detail=True` for full) | User wants to compare or survey |
| `paper_compare` | Structured comparison data | User says "对比这几篇论文" |
| `paper_search_online` | Search arXiv + Semantic Scholar in real-time (covers conferences!) | Local results insufficient, or need conference papers |
| `paper_download` | Batch download PDFs (pass multiple IDs at once) | User wants to download papers |
| `paper_export` | Export to BibTeX/markdown/JSON | User says "导出 BibTeX" |
| `paper_survey_collect` | Collect papers over N years for survey | User wants to survey a research topic |

## MCP Resources

| URI | Content |
|-----|---------|
| `paper://digest/today` | Today's digest |
| `paper://stats` | Library stats |
| `paper://profile` | Research interests |
| `paper://recent` | Papers from last 7 days |

## Workflows

### Start My Day

1. `paper_collect(days=1)` → fetch latest papers
2. `paper_digest()` → generate recommendations
3. Present in Chinese: overview → high-confidence picks → reading advice

### Paper Search

1. `paper_search(query)` → search library
2. **Check suggestions**: if results have `suggestions` field:
   - `diverse_search`: re-run with `paper_search(query, diverse=True)` for keyword expansion
   - `online_search`: use `paper_search_online(query)` — searches arXiv + Semantic Scholar in parallel, covering both preprints and conference papers
   - `collect_first`: suggest `paper_collect()` to populate the library first
3. Show concise list: title, score, one-line summary
4. `paper_show(paper_id)` for deep dive on request
5. For conference papers specifically, `paper_search_online(query, sources=["s2"])` targets Semantic Scholar which indexes all major venues

### Paper Analyze

1. `paper_show(paper_id)` → get paper details
2. Generate structured analysis note (see [references/analysis-template.md](references/analysis-template.md))
3. Include: core info, translated abstract, method overview, experiments, critique, comparison
4. Ask if user wants to save to file

### Paper Compare

1. If user provides paper IDs, use them; otherwise search or ask
2. Ask dimensions: a) 方法架构  b) 实验结果  c) 适用场景  d) 全部
3. `paper_batch_show(paper_ids)` → get all details
4. `paper_compare(paper_ids, aspects)` → get structured comparison data
5. Generate comparison table in Chinese:
   | 论文 | 方法 | 关键技术 | 主要结果 | 适用场景 |
6. Provide analysis summary: which approach is best for what scenario
7. Ask: "要保存对比表格吗？或者基于这些写 survey？"
8. If export requested, `paper_export(paper_ids, format="bibtex")`

### Paper Survey (single topic)

1. Parse topic from user request, extract keywords
2. `paper_survey_collect(keywords, venues, years_back)` → collect papers over N years from arXiv + DBLP + S2
3. `paper_search(topic)` → also search local library
4. If results insufficient, `paper_search_online(query)` for additional papers
5. Present candidate list, let user select which to include
6. Ask sections: Background, 方法分类与对比, 实验结果汇总, Future Directions, or 全部
7. `paper_batch_show(selected_ids)` → get full details
8. Generate survey in Chinese with proper citations:
   - 引言与背景
   - 方法分类 (taxonomy)
   - 各方法详解与对比表格
   - 实验对比
   - 研究空白与未来方向
   - 参考文献
9. Iterate on user feedback
10. `paper_export(ids, format="bibtex")` → export references

### Multi-Topic Survey (multiple directions)

When user asks to survey/compare **multiple research directions** at once
(e.g. "4 directions x 20 papers each, write a survey"):

1. Extract the N direction keywords from the user's request
2. `paper_search_batch(queries=[dir1, dir2, ...], limit_per_query=20, diverse=True)` → search all directions in one call, get results grouped by topic
3. For each direction, pick representative papers from the grouped results
4. `paper_batch_show(all_selected_ids)` → get full details for all selected papers
5. Generate the survey organized by direction, with cross-direction comparison
6. `paper_export(all_ids, format="bibtex")` → export references

**IMPORTANT**: Never use `/paper-analyze` for multi-paper tasks. `/paper-analyze` is for single-paper deep dives only. Use `/paper-survey` or `/paper-compare` for multi-paper work.

### Paper Download (supports batch)

1. Parse paper ID(s) or search query from user
2. If query, search first and ask which papers to download
3. `paper_download(paper_ids)` → pass ALL IDs in one call for batch download
4. Report results: ✅ downloaded / ⏭️ existed / ❌ failed
5. Ask: "要阅读哪篇？"

NOTE: `paper_download` accepts a list — always pass all IDs at once, never call it once per paper.

### Coding Context

When user works on AI/ML code, watch for:
- arXiv ID patterns (`2301.12345`)
- Method names (attention, BERT, LoRA, transformer, GNN, diffusion, etc.)

Proactively suggest: "检测到你在讨论 [技术], 要查看相关论文吗？"

## Output Rules

1. **Chinese first** for all analysis and summaries
2. **Wikilink format**: `[[论文标题]]` for knowledge base linking
3. **Concise by default**, full detail only for deep analysis
4. **No duplicate work**: reference existing notes if available
5. **Always suggest next step**: after each action, suggest what to do next

## First-Time Setup

```bash
paper-agent init          # Configure LLM (terminal only)
```

Then in IDE, say "配置研究方向" → AI will guide profile setup via conversation.
