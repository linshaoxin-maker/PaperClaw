---
description: Download PDF files for papers from arXiv
argument-hint: <paper_id or search query>
allowed-tools: [
  "mcp__plugin_paper-agent_paper-agent__paper_search",
  "mcp__plugin_paper-agent_paper-agent__paper_show",
  "mcp__plugin_paper-agent_paper-agent__paper_download"
]
---

# Paper Download

Download PDF files for one or more papers.

## Process

1. Parse $ARGUMENTS as paper ID(s) or a search query
2. If it looks like a paper ID (e.g., 2301.12345), download directly
3. If it's a query, search first and ask which papers to download
4. Call `paper_download(paper_ids)` to download PDFs
5. Report results in Chinese:
   - ✅ 已下载: filename, path
   - ⏭️ 已存在: filename
   - ❌ 失败: reason
6. Ask: "要阅读哪篇？"
