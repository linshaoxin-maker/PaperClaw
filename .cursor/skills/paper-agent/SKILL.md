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
| `paper_search` | Full-text search in local library | User asks about a paper, method, or technique |
| `paper_show` | Full details for a specific paper (supports bare arXiv IDs) | User wants to dive into one paper |
| `paper_collect` | Fetch from arXiv + LLM scoring | User says "收集论文" or "update library" |
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
| `paper_batch_show` | Get details for multiple papers | User wants to compare or survey several papers |
| `paper_compare` | Structured comparison data | User says "对比这几篇论文" |
| `paper_search_online` | Search arXiv API in real-time | Local results insufficient |
| `paper_download` | Download PDF files from arXiv | User wants to download papers |
| `paper_export` | Export to BibTeX/markdown/JSON | User says "导出 BibTeX" |

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
2. Show concise list: title, score, one-line summary
3. If insufficient: ask user → `paper_search_online(query)` to search arXiv
4. `paper_show(paper_id)` for deep dive on request

### Paper Analyze

1. `paper_show(paper_id)` → get paper details
2. Generate structured analysis note (see [references/analysis-template.md](references/analysis-template.md))
3. Include: core info, translated abstract, method overview, experiments, critique, comparison
4. Ask if user wants to save to file

### Paper Compare (v02)

1. `paper_batch_show(paper_ids)` → get all papers
2. Ask user which dimensions to compare (method, result, application, architecture)
3. `paper_compare(paper_ids, aspects)` → get structured data
4. Generate comparison table and analysis in Chinese
5. Ask: save? write survey?

### Paper Survey (v02)

1. Search and select papers
2. `paper_batch_show(ids)` → get details
3. Generate survey with sections: background, method taxonomy, experiments, future directions
4. Iterate on feedback
5. `paper_export(ids, format="bibtex")` → export references

### Coding Context

When user works on AI/ML code, watch for:
- arXiv ID patterns (`2301.12345`)
- Method names (attention, BERT, LoRA, transformer)

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
