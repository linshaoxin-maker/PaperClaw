---
name: paper-intelligence
description: AI research paper intelligence for daily workflow. Use when the user mentions paper, arxiv, digest, research paper, 论文, 论文分析, start my day, paper-analyze, paper-compare, paper-survey, arXiv IDs (like 2301.12345), ML method names, or asks about academic research trends. Provides contextual paper search, recommendation, deep analysis, multi-paper comparison, and survey generation via MCP tools.
version: 0.2.0
---

# Paper Intelligence

Contextual paper intelligence powered by the paper-agent MCP server.

## Available MCP Tools

### Core (v01 — single-paper)

| Tool | Purpose |
|------|---------|
| `paper_search` | Full-text search in local library |
| `paper_show` | Get full details of a specific paper (supports bare arXiv IDs) |
| `paper_collect` | Fetch papers from arXiv + LLM scoring |
| `paper_digest` | Generate daily recommendations |
| `paper_stats` | Library statistics |
| `paper_profile` | Current research profile |
| `paper_profile_update` | Create/update profile via conversation |
| `paper_sources_list` | List all available sources |
| `paper_sources_enable` | Enable/disable sources |
| `paper_templates_list` | List research area templates |

### Multi-Paper Intelligence (v02)

| Tool | Purpose |
|------|---------|
| `paper_batch_show` | Get details for multiple papers at once |
| `paper_compare` | Structured comparison data for multiple papers |
| `paper_search_online` | Search arXiv API in real-time (beyond local library) |
| `paper_download` | Download PDF files from arXiv |
| `paper_export` | Export to BibTeX / markdown / JSON |

## When to Use

- User mentions a paper, method, or arXiv ID → `paper_search` or `paper_show`
- User says "start my day" or "今日推荐" → `paper_collect` + `paper_digest`
- User is working on AI/ML code and mentions a technique → suggest searching related papers
- User asks "分析论文" or "paper-analyze" → `paper_show` + structured analysis
- User wants to compare papers → `paper_compare` + `paper_batch_show`
- User asks for a survey → `paper_batch_show` + `paper_export`
- User wants to download PDFs → `paper_download`
- User wants to search beyond local library → `paper_search_online`

## Coding Context Integration

When the user is coding in AI/ML projects, watch for:

- arXiv ID patterns (e.g., `2301.12345`)
- Method references (e.g., "attention mechanism", "BERT", "LoRA")
- Research terminology in comments or variable names

Proactively suggest: "检测到你在讨论 [技术], 要查看本地库中的相关论文吗？"

## Output Rules

1. **Chinese first**: All analysis and summaries in Chinese
2. **Wikilink format**: Paper titles as `[[论文标题]]` for knowledge base linking
3. **Concise by default**: Brief results for search, full detail only for deep analysis
4. **No duplicate work**: If a paper already has notes, reference existing content
5. **Always suggest next step**: After each action, suggest what to do next

## Available Commands

| Command | Purpose |
|---------|---------|
| `/start-my-day` | Collect + digest + recommendations |
| `/paper-search <query>` | Search local library |
| `/paper-analyze <id>` | Deep analysis of one paper |
| `/paper-collect [days]` | Collect from arXiv |
| `/paper-setup` | Guided profile creation |
| `/paper-compare` | Compare multiple papers |
| `/paper-survey <topic>` | Generate literature survey |
| `/paper-download <id>` | Download PDF files |

## First-Time Setup

```bash
pip install paper-agent    # or: pipx install paper-agent
paper-agent init           # Configure LLM provider
```

Then use `/paper-setup` to create your research profile via conversation.

## Detailed Templates

For the full analysis note template, see [references/analysis-template.md](references/analysis-template.md).
