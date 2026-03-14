"""paper-agent setup ... commands — configure IDE integration."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from paper_agent.cli.console import console, print_error, print_success

setup_app = typer.Typer(
    name="setup",
    help="Configure IDE integration (Cursor / Claude Code).",
)


# ── Helpers ───────────────────────────────────────────────────────


def _resolve_mcp_command() -> tuple[str, list[str]]:
    """Find the best way to invoke the MCP server.

    Resolution order:
    1. ``paper-agent-mcp`` on PATH  → portable name
    2. Same binary dir as current Python (venv) → absolute path
    3. Fallback: current python ``-m paper_agent.mcp``
    """
    which = shutil.which("paper-agent-mcp")
    if which:
        return "paper-agent-mcp", []

    venv_bin = Path(sys.executable).parent / "paper-agent-mcp"
    if venv_bin.exists():
        return str(venv_bin), []

    return sys.executable, ["-m", "paper_agent.mcp"]


def _merge_mcp_json(path: Path, cmd: str, args: list[str]) -> None:
    """Write or merge paper-agent entry into an MCP config file."""
    existing: dict = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    servers = existing.get("mcpServers", {})
    servers["paper-agent"] = {"command": cmd, "args": args}
    existing["mcpServers"] = servers

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n")


def _init_workspace(target: Path) -> None:
    """Create .paper-agent/ workspace directory in the project."""
    from paper_agent.services.workspace_manager import WorkspaceManager

    ws_dir = target / ".paper-agent"
    ws = WorkspaceManager(ws_dir, storage=None)  # type: ignore[arg-type]
    result = ws.init()
    if result["status"] == "initialized":
        print_success(f"Workspace → {ws_dir}")
    elif result["status"] == "repaired":
        print_success(f"Workspace → {ws_dir} (补全了缺失文件)")
    else:
        console.print(f"  [dim]Workspace 已存在 → {ws_dir}[/dim]")


# ── Cursor ────────────────────────────────────────────────────────


@setup_app.command("cursor")
def setup_cursor(
    scope: str = typer.Option(
        "project",
        "--scope", "-s",
        help="project = current dir (.cursor/), global = ~/.cursor/",
    ),
    project_dir: Optional[str] = typer.Option(
        None, "--project-dir", help="Target project directory (default: cwd)"
    ),
) -> None:
    """Configure paper-agent for Cursor IDE."""
    cmd, args = _resolve_mcp_command()

    if scope == "project":
        target = Path(project_dir) if project_dir else Path.cwd()
        _setup_cursor_project(target, cmd, args)
    elif scope == "global":
        _setup_cursor_global(cmd, args)
    else:
        print_error("--scope 必须是 'project' 或 'global'")
        raise typer.Exit(1)

    console.print("\n[bold]下一步：[/bold]")
    console.print("  1. 重启 Cursor（或 Cmd+Shift+P → Reload Window）")
    console.print("  2. 在 Agent chat 中说 [cyan]\"start my day\"[/cyan] 或 [cyan]\"搜索论文 transformer\"[/cyan]")
    console.print("  3. Agent 会自动调用 paper-agent MCP 工具\n")


def _setup_cursor_project(target: Path, cmd: str, args: list[str]) -> None:
    cursor_dir = target / ".cursor"

    mcp_path = cursor_dir / "mcp.json"
    _merge_mcp_json(mcp_path, cmd, args)
    print_success(f"MCP → {mcp_path}")

    skill_dir = cursor_dir / "skills" / "paper-agent"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(_CURSOR_SKILL)
    ref_dir = skill_dir / "references"
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / "analysis-template.md").write_text(_ANALYSIS_TEMPLATE)
    print_success(f"Skill → {skill_dir / 'SKILL.md'}")

    rule_dir = cursor_dir / "rules"
    rule_dir.mkdir(parents=True, exist_ok=True)
    (rule_dir / "paper-agent.mdc").write_text(_CURSOR_RULE)
    print_success(f"Rule  → {rule_dir / 'paper-agent.mdc'}")

    _init_workspace(target)


def _setup_cursor_global(cmd: str, args: list[str]) -> None:
    cursor_home = Path.home() / ".cursor"
    if not cursor_home.exists():
        print_error("~/.cursor 不存在。请确认已安装 Cursor IDE。")
        raise typer.Exit(1)

    mcp_path = cursor_home / "mcp.json"
    _merge_mcp_json(mcp_path, cmd, args)
    print_success(f"MCP → {mcp_path}")

    skill_dir = cursor_home / "skills" / "paper-agent"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(_CURSOR_SKILL)
    ref_dir = skill_dir / "references"
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / "analysis-template.md").write_text(_ANALYSIS_TEMPLATE)
    print_success(f"Skill → {skill_dir / 'SKILL.md'}")

    rule_dir = cursor_home / "rules"
    rule_dir.mkdir(parents=True, exist_ok=True)
    (rule_dir / "paper-agent.mdc").write_text(_CURSOR_RULE)
    print_success(f"Rule  → {rule_dir / 'paper-agent.mdc'}")


# ── Claude Code ───────────────────────────────────────────────────


@setup_app.command("claude-code")
def setup_claude_code(
    scope: str = typer.Option(
        "project",
        "--scope", "-s",
        help="project = .mcp.json + .claude/ commands, global = claude mcp add",
    ),
    project_dir: Optional[str] = typer.Option(
        None, "--project-dir", help="Target project directory (default: cwd)"
    ),
) -> None:
    """Configure paper-agent for Claude Code CLI."""
    cmd, args = _resolve_mcp_command()

    if scope == "project":
        target = Path(project_dir) if project_dir else Path.cwd()
        _setup_claude_project(target, cmd, args)
    elif scope == "global":
        _setup_claude_global(cmd, args)
    else:
        print_error("--scope 必须是 'project' 或 'global'")
        raise typer.Exit(1)


def _setup_claude_project(target: Path, cmd: str, args: list[str]) -> None:
    mcp_path = target / ".mcp.json"
    _merge_mcp_json(mcp_path, cmd, args)
    print_success(f"MCP → {mcp_path}")

    commands_dir = target / ".claude" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)
    for name, content in _CLAUDE_COMMANDS.items():
        (commands_dir / name).write_text(content)
    print_success(
        f"Commands → {commands_dir}  "
        "(/start-my-day, /paper-search, /paper-analyze, /paper-collect, "
        "/paper-setup, /paper-compare, /paper-survey, /paper-download)"
    )

    claude_md = target / "CLAUDE.md"
    if not claude_md.exists():
        claude_md.write_text(_CLAUDE_MD)
        print_success(f"CLAUDE.md → {claude_md}")
    else:
        console.print(f"  [dim]CLAUDE.md 已存在，跳过[/dim]")

    _init_workspace(target)

    console.print("\n[bold]下一步：[/bold]")
    console.print(f"  1. 在 [cyan]{target}[/cyan] 目录运行 [cyan]claude[/cyan]")
    console.print("  2. 试试 [cyan]/start-my-day[/cyan] 命令")
    console.print("  3. 或直接说 [cyan]\"搜索论文 transformer\"[/cyan]\n")


def _setup_claude_global(cmd: str, args: list[str]) -> None:
    claude_bin = shutil.which("claude")
    if not claude_bin:
        print_error("未找到 claude CLI。")
        console.print("安装: [cyan]curl -fsSL https://claude.ai/install.sh | bash[/cyan]")
        raise typer.Exit(1)

    run_args = ["claude", "mcp", "add", "paper-agent", "--transport", "stdio", "--", cmd, *args]
    console.print(f"  运行: [dim]{' '.join(run_args)}[/dim]")

    try:
        result = subprocess.run(run_args, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print_success("MCP server 已注册到 Claude Code（全局）。")
        else:
            print_error(f"claude mcp add 失败: {result.stderr.strip()}")
            console.print("可手动运行:")
            console.print(f"  [cyan]{' '.join(run_args)}[/cyan]")
            raise typer.Exit(1)
    except FileNotFoundError:
        print_error("无法执行 claude CLI。")
        raise typer.Exit(1)
    except subprocess.TimeoutExpired:
        print_error("claude mcp add 超时。请手动运行上述命令。")
        raise typer.Exit(1)

    console.print("\n[bold]下一步：[/bold]")
    console.print("  1. 在任意目录运行 [cyan]claude[/cyan]")
    console.print("  2. 直接说 [cyan]\"搜索论文 transformer\"[/cyan] 使用 paper-agent 工具\n")


# ═══════════════════════════════════════════════════════════════════
# Embedded templates — self-contained, no path dependencies
# ═══════════════════════════════════════════════════════════════════

_CURSOR_SKILL = """\
---
name: paper-agent
description: >-
  AI research paper intelligence assistant — collect, recommend, search,
  analyze, compare, and survey arXiv papers via MCP. Use when the user
  mentions paper, arxiv, digest, research, 论文, 论文分析, 论文对比, 写综述,
  start my day, paper-analyze, paper-compare, paper-survey, arXiv IDs
  (like 2301.12345), ML method names, or asks about academic research trends.
---

# Paper Agent

Research paper intelligence powered by the paper-agent MCP server.

## MCP Tools

### Core (v01)

| Tool | Purpose | Typical Trigger |
|------|---------|-----------------|
| `paper_search` | FTS search with keyword expansion (`diverse` mode) | User asks about a paper or method |
| `paper_show` | Full details for a specific paper | User wants to dive into one paper |
| `paper_collect` | Fetch from arXiv + DBLP + S2 concurrently | User says "收集论文" |
| `paper_digest` | Daily recommendations | User says "今日推荐" or "start my day" |
| `paper_stats` | Library statistics | User asks "库里有多少论文" |
| `paper_profile` | View research profile | User asks "我的研究方向" |
| `paper_profile_update` | Create/update profile via conversation | User describes research interests |
| `paper_sources_list` | List all available sources | User asks about arXiv categories |
| `paper_sources_enable` | Enable/disable sources | User wants to add/remove categories |
| `paper_templates_list` | List research area templates | User wants a preset template |

### Multi-Paper Intelligence (v02)

| Tool | Purpose | Typical Trigger |
|------|---------|-----------------|
| `paper_search_batch` | Search multiple topics at once (grouped results) | User wants to survey/compare N directions |
| `paper_batch_show` | Get papers info (compact default, `detail=True` for full) | User wants to compare or survey |
| `paper_compare` | Structured comparison data | User says "对比这几篇论文" |
| `paper_search_online` | Search arXiv + S2 online (covers conferences!) | Local results insufficient |
| `paper_download` | Batch download PDFs (pass multiple IDs) | User wants to download papers |
| `paper_export` | Export to BibTeX/markdown/JSON | User says "导出 BibTeX" |
| `paper_survey_collect` | Collect papers over N years for survey | User wants to survey a topic |

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
   - `online_search`: suggest `paper_search_online(query)` for real-time arXiv results
   - `collect_first`: suggest `paper_collect()` to populate library
3. Show concise list: title, score, one-line summary
4. `paper_show(paper_id)` for deep dive on request

### Paper Analyze
1. `paper_show(paper_id)` → get paper details
2. Generate structured analysis note (see [analysis template](references/analysis-template.md))
3. Include: core info, translated abstract, method overview, experiments, critique

### Paper Compare
1. If user provides paper IDs, use them; otherwise search or ask
2. Ask dimensions: a) 方法架构  b) 实验结果  c) 适用场景  d) 全部
3. `paper_batch_show(paper_ids)` + `paper_compare(paper_ids, aspects)`
4. Generate comparison table in Chinese
5. Ask: "要保存对比表格吗？或者基于这些写 survey？"

### Paper Survey (single topic)
1. Parse topic → extract keywords
2. `paper_survey_collect(keywords, venues, years_back)` → collect from arXiv + DBLP + S2
3. `paper_search(topic)` + optionally `paper_search_online(query)`
4. `paper_batch_show(selected_ids)` → get full details
5. Generate survey: 引言, 方法分类, 实验对比, 未来方向, 参考文献
6. `paper_export(ids, format="bibtex")` → export references

### Multi-Topic Survey (multiple directions)
When user asks to survey/compare multiple directions at once:
1. Extract the N direction keywords
2. `paper_search_batch(queries=[dir1, dir2, ...], limit_per_query=20, diverse=True)` → search all at once
3. Pick representative papers from each group
4. `paper_batch_show(all_ids)` → get full details
5. Generate survey organized by direction with cross-direction comparison
6. `paper_export(all_ids, format="bibtex")`

IMPORTANT: Never use /paper-analyze for multi-paper tasks. Use /paper-survey or /paper-compare.

### Paper Download
1. Parse paper ID(s) or search query
2. `paper_download(paper_ids)` → download PDFs
3. Report results: ✅ downloaded / ⏭️ existed / ❌ failed

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

If paper-agent is not initialized, guide the user:

```bash
paper-agent init            # Configure LLM
paper-agent profile create  # Set research interests
paper-agent collect -d 7    # Initial collection
```
"""

_CURSOR_RULE = """\
---
description: >-
  Auto-activate paper-agent MCP tools when user mentions papers, arXiv,
  research digests, or uses paper-related keywords.
globs:
alwaysApply: false
---

# Paper Agent Rule

当检测到以下场景时，自动激活 paper-agent MCP 工具：

## 触发条件

### 日常推荐
- 用户说 "start my day" 或 "今日推荐" → `paper_collect(days=1)` + `paper_digest()`

### 搜索
- 用户说 "搜索论文" / "paper search" + 关键词 → `paper_search(query)`
- 结果少时建议用户使用 `paper_search(query, diverse=True)` 扩展关键词
- 本地不够时建议 `paper_search_online(query)` 在线搜索

### 采集
- 用户说 "收集论文" / "paper collect" → `paper_collect()`

### 单篇分析
- 用户说 "分析论文" / "paper-analyze" + ID → `paper_show(paper_id)` 并生成分析笔记
- 用户提到 arXiv ID 格式（如 `2301.12345`）→ `paper_show()`

### 多篇对比
- 用户说 "对比论文" / "论文比较" / "paper compare" → `paper_batch_show` + `paper_compare`
- 用户说 "这几篇有什么区别" / "比一下方法" → 同上

### 文献综述
- 用户说 "写综述" / "literature survey" / "paper survey" → Survey 工作流
- 用户说 "这个方向有哪些工作" / "梳理一下研究现状" → 同上

### 下载
- 用户说 "下载论文" / "paper download" → `paper_download(paper_ids)`

### 导出
- 用户说 "导出 BibTeX" / "export" → `paper_export(paper_ids, format)`

### 编码上下文
- 用户在 AI/ML 代码中提到方法名（transformer, attention, BERT, LoRA, GNN 等）→ 建议搜索相关论文

## 行为规范

- 所有论文分析和摘要使用中文输出
- 论文标题使用 `[[论文标题]]` wikilink 格式
- 搜索结果保持精简，深度分析才展开全部内容
- 如果 paper-agent 未初始化，引导用户运行 `paper-agent init`
- 搜索结果少时主动提示：可以尝试 `diverse=True` 扩展关键词，或在线搜索
"""

_ANALYSIS_TEMPLATE = """\
# Paper Analysis Note Template

Use this template when generating deep analysis notes for papers.

## Frontmatter

```yaml
---
date: {{date}}
paper_id: {{paper_id}}
title: "{{title}}"
authors: [{{authors}}]
domain: {{domain}}
tags: [{{tags}}]
quality_score: {{score}}/10
status: reading
---
```

## Note Structure

### 核心信息
- **标题**: {{title}}
- **作者**: {{authors}}
- **机构**: {{affiliations}}
- **发表**: {{venue}} {{year}}
- **链接**: [arXiv]({{url}}) | [PDF]({{pdf_url}})

### 摘要翻译
> （中文翻译的摘要）

### 要点提炼
1. （核心贡献 1）
2. （核心贡献 2）
3. （核心贡献 3）

### 研究背景与动机
（为什么做这个研究？解决什么问题？）

### 方法概述
#### 核心思想
（一句话概括方法）

#### 方法框架
（整体架构描述）

#### 各模块详细说明
（关键模块的技术细节）

### 实验结果
#### 主要结果
（核心实验数据和对比）

#### 消融实验
（各模块的贡献分析）

### 深度分析
#### 研究价值评估
（对领域的贡献程度）

#### 方法优势
（相比现有方法的优势）

#### 局限性
（方法的不足和限制）

#### 适用场景
（最适合应用的场景）

### 与相关论文对比
| 论文 | 方法 | 优势 | 不足 |
|------|------|------|------|
| 本文 | | | |
| 对比 1 | | | |

### 未来工作建议
1. （可能的改进方向）

### 我的笔记
（个人理解和想法）
"""

_CLAUDE_MD = """\
# Paper Agent

This project uses **paper-agent** MCP server for research paper intelligence.

## Available MCP Tools

### Core Tools (v01 — single-paper)
- `paper_search(query, diverse=False)` — search local library (diverse=True expands keywords via synonyms)
- `paper_show(paper_id)` — show paper details (accepts arXiv IDs like `2301.12345`)
- `paper_collect(days)` — collect from arXiv + DBLP + Semantic Scholar concurrently
- `paper_digest()` — generate daily recommendations
- `paper_stats()` — library statistics

### Multi-Paper Intelligence (v02)
- `paper_search_batch(queries, limit_per_query)` — search multiple topics at once (for surveys)
- `paper_batch_show(paper_ids)` — get details for multiple papers at once
- `paper_compare(paper_ids, aspects)` — structured comparison data for multiple papers
- `paper_search_online(query, sources=["arxiv","s2"])` — search arXiv + Semantic Scholar online (covers conferences!)
- `paper_survey_collect(keywords, venues, years_back)` — collect papers over N years for survey
- `paper_download(paper_ids)` — download PDF files from arXiv
- `paper_export(paper_ids, format)` — export to BibTeX / markdown / JSON

### Profile & Sources Management
- `paper_profile()` — view current research profile
- `paper_profile_update(topics, keywords, enable_sources)` — create/update profile via conversation
- `paper_sources_list()` — list all available sources (arXiv categories, conferences)
- `paper_sources_enable(enable, disable)` — enable/disable specific sources
- `paper_templates_list()` — list research area templates for quick profile setup

## Custom Commands

### Daily Workflow
- `/start-my-day` — collect today's papers + generate digest
- `/paper-search <query>` — search the library
- `/paper-analyze <paper_id>` — deep analysis of a paper
- `/paper-collect [days]` — collect from arXiv + DBLP + S2
- `/paper-setup` — guided profile creation through conversation

### Multi-Paper Workflows (v02)
- `/paper-compare` — compare multiple papers side by side
- `/paper-survey <topic>` — generate literature survey from papers
- `/paper-download <id>` — download PDF files from arXiv

## Interaction Principles

Every workflow follows the same loop:
1. User initiates (natural language or slash command)
2. AI understands intent → confirms/clarifies
3. Calls MCP tool(s) → gets data
4. Formats results (Chinese, tables, wikilinks)
5. Suggests next step ("保存吗？" "继续分析？" "写 survey？")
6. User responds → loop

## Output Conventions

- Use **Chinese** for all paper analysis and summaries
- Use `[[论文标题]]` wikilink format for knowledge base linking
- Keep search results concise; expand only for deep analysis
- After analysis, ask if user wants to save to file
- After comparison, suggest writing a survey
- Search results that include `suggestions` → follow them proactively

## First-Time Setup

```bash
paper-agent init            # Configure LLM provider and API key (terminal only)
```

Then in Claude Code:
```
/paper-setup                # Create research profile via conversation
```
"""

_CLAUDE_COMMANDS: dict[str, str] = {
    "start-my-day.md": """\
---
description: Collect latest arXiv papers and generate today's personalized digest
allowed-tools: [
  "mcp__paper-agent__paper_collect",
  "mcp__paper-agent__paper_digest",
  "mcp__paper-agent__paper_stats"
]
---

# Start My Day

Generate today's personalized paper digest.

## Process

1. Call `paper_collect(days=1)` to fetch the latest papers from arXiv
2. Call `paper_digest()` to generate today's recommendations
3. Present results in Chinese:
   - **今日概览**: total collected, new papers, scoring summary
   - **高置信推荐**: top papers with title, score, one-line reason
   - **阅读建议**: which papers to prioritize and why
""",
    "paper-search.md": """\
---
description: Search the local paper library by keyword, topic, or method name
argument-hint: <query>
allowed-tools: [
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_show"
]
---

# Paper Search

Search the local paper library.

## Process

1. Parse $ARGUMENTS as the search query
2. Call `paper_search(query=$ARGUMENTS)` to search the library
3. Present results as a concise list — each paper with title, score, and one-line summary
4. If the user asks about a specific paper from the results, call `paper_show(paper_id)` for details

## Output Format

找到 N 篇相关论文：

| # | 标题 | 评分 | 摘要 |
|---|------|------|------|
| 1 | ... | 8.5 | ... |

需要查看某篇的详细信息吗？
""",
    "paper-analyze.md": """\
---
description: Generate a structured deep-analysis note for a specific paper
argument-hint: <paper_id or arxiv_id>
allowed-tools: [
  "mcp__paper-agent__paper_show",
  "mcp__paper-agent__paper_search",
  "Bash",
  "Read",
  "Write"
]
---

# Paper Analyze

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
   - **深度分析**: value, strengths, limitations, use cases
   - **与相关论文对比**: comparison table
   - **未来工作建议**: potential improvements
""",
    "paper-collect.md": """\
---
description: Collect papers from arXiv and run LLM relevance scoring
argument-hint: [days_back]
allowed-tools: [
  "mcp__paper-agent__paper_collect",
  "mcp__paper-agent__paper_stats"
]
---

# Paper Collect

Collect papers from configured arXiv categories.

## Process

1. Parse $ARGUMENTS for optional `days_back` parameter (default: 7)
2. Call `paper_collect(days=$days_back)` to fetch and score papers
3. Call `paper_stats()` to show updated library overview
4. Present results in Chinese:
   - **收集完成**: N papers collected (X new, Y duplicate)
   - **库概览**: total papers, high/low confidence counts
   - **热门主题**: top topics from the library
""",
    "paper-setup.md": """\
---
description: Set up research profile through conversation — determine research interests and configure sources
allowed-tools: [
  "mcp__paper-agent__paper_profile",
  "mcp__paper-agent__paper_profile_update",
  "mcp__paper-agent__paper_templates_list",
  "mcp__paper-agent__paper_sources_list",
  "mcp__paper-agent__paper_sources_enable",
  "mcp__paper-agent__paper_collect"
]
---

# Paper Setup

Guide the user through creating their research profile via conversation.

## Process

1. Call `paper_profile()` to check if a profile already exists
2. If profile exists, show current topics/keywords and ask if user wants to update
3. Ask the user about their research interests in a natural conversation:
   - What are your research areas?
   - What techniques or methods do you focus on?
4. Optionally call `paper_templates_list()` to show available templates
   - If a template matches, use its topics/keywords as a starting point
5. Extract topics and keywords from the conversation
6. Call `paper_sources_list()` to show available arXiv categories
7. Recommend relevant sources based on the user's interests
8. Call `paper_profile_update(topics, keywords, enable_sources)` to save
9. Ask if the user wants to do an initial collection:
   - If yes, call `paper_collect(days=7)`

## Conversation Style

- Use Chinese for all communication
- Be conversational, not a form to fill out
- Suggest topics/keywords proactively based on what the user describes
- Explain what sources are and why they matter
""",
    "paper-compare.md": """\
---
description: Compare multiple papers side by side — methods, results, architecture
allowed-tools: [
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_batch_show",
  "mcp__paper-agent__paper_compare",
  "mcp__paper-agent__paper_export",
  "Write"
]
---

# Paper Compare

Compare multiple papers on selected dimensions.

## Process

1. If $ARGUMENTS contains paper IDs, use them directly
2. Otherwise, ask the user which papers to compare
   - Optionally search first: `paper_search(query)` to find candidates
3. Ask which dimensions to compare:
   - a) 方法架构  b) 实验结果  c) 适用场景  d) 全部
4. Call `paper_compare(paper_ids, aspects)` to get structured comparison data
5. Generate a comparison table in Chinese:
   | 论文 | 方法 | 关键技术 | 主要结果 | 适用场景 |
6. Provide analysis summary: which approach is best for what scenario
7. Ask: "要保存对比表格吗？或者基于这些写 survey？"
8. If save requested, write to file
9. If export requested, call `paper_export(paper_ids, format="bibtex")`
""",
    "paper-survey.md": """\
---
description: Generate a literature survey from selected papers
argument-hint: <topic>
allowed-tools: [
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_search_online",
  "mcp__paper-agent__paper_survey_collect",
  "mcp__paper-agent__paper_batch_show",
  "mcp__paper-agent__paper_compare",
  "mcp__paper-agent__paper_export",
  "Write"
]
---

# Paper Survey

Generate a structured literature survey around a research topic.

## Process

1. Parse $ARGUMENTS as the survey topic
2. Analyze the topic — extract keywords, expand search terms, confirm with user
3. Search for papers:
   - `paper_search(query)` for local library
   - If results insufficient, ask user: "本地找到 N 篇，要从 arXiv 在线补充搜索吗？"
   - If yes, `paper_search_online(query)` for additional papers
4. Present candidate list and let user select which to include
5. Ask which sections to include:
   - a) Background & Motivation
   - b) 方法分类与对比
   - c) 实验结果汇总
   - d) Open Problems & Future Directions
   - e) 全部
6. Call `paper_batch_show(selected_ids)` to get full details
7. Generate the survey in Chinese with proper citations
8. Show draft and ask for feedback: "需要修改哪里？"
9. Iterate based on feedback
10. Ask save path and write to file
11. Offer to export BibTeX: `paper_export(ids, format="bibtex")`

## Output Format

Survey should include:
- 引言与背景
- 方法分类 (taxonomy)
- 各方法详解与对比表格
- 实验对比
- 研究空白与未来方向
- 参考文献
""",
    "paper-download.md": """\
---
description: Download PDF files for papers from arXiv
argument-hint: <paper_id or search query>
allowed-tools: [
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_show",
  "mcp__paper-agent__paper_download"
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
""",
}