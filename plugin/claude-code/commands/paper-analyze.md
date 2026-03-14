---
description: Generate a structured deep-analysis note for a specific paper
argument-hint: <paper_id or arxiv_id>
allowed-tools: [
  "mcp__paper-agent__paper_show",
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_note_add",
  "Bash",
  "Read",
  "Write"
]
---

# Paper Analyze

> Workflow detail: read `.claude/skills/deep-dive/SKILL.md` for full analysis template, fork rules, and edge cases.

Generate a structured deep-analysis note for a paper.

## Process

1. Parse $ARGUMENTS as `paper_id` (e.g., `2301.12345` or `arxiv:2301.12345`)
2. Call `paper_show(paper_id)` to get full paper details
3. If not found, try `paper_search(query=$ARGUMENTS)` and pick the best match
4. Generate a structured analysis note in Chinese with these sections:
   - **核心信息**: title, authors, venue, links
   - **摘要翻译**: Chinese translation of the abstract
   - **要点提炼**: 3 key contributions
   - **研究背景与动机**: why this research matters
   - **方法概述**: core idea, framework, key modules
   - **实验结果**: main results + ablation studies
   - **深度分析**: value, strengths, limitations, use cases (use table for strengths/limitations)
   - **与相关论文对比**: comparison table (| 维度 | 本文 | 对比1 | 对比2 |)
   - **结论与建议**: 研究价值判断 + 与用户研究方向的关联 + 值不值得深入跟进
5. Auto-track: call `paper_note_add(paper_id, content, mark_as="reading")` to save to workspace
6. **ASK**: "要导出分析笔记为文件？看引用链？还是先这样？"
