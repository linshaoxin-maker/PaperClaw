---
description: Download PDF files for papers from arXiv
argument-hint: <paper_id or search query>
allowed-tools: [
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_show",
  "mcp__paper-agent__paper_download",
  "mcp__paper-agent__paper_find_and_download"
]
---

# Paper Download

Download PDF files for one or more papers.

## Process

1. Parse $ARGUMENTS as paper ID(s), title, or a search query
2. If it looks like a paper ID (e.g., 2301.12345), call `paper_download(paper_ids)`
3. If it looks like a paper title, call `paper_find_and_download(title=$ARGUMENTS)`
4. If it's a query, search first and ask which papers to download
5. Report results in Chinese
