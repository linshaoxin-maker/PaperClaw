"""paper-agent setup ... commands — configure IDE integration."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from paper_agent.cli._skill_content import (
    ROUTER_SKILL,
    SKILL_TEMPLATES,
    TEMPLATE_FILENAMES,
    WORKFLOW_SKILLS,
)
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


def _write_cursor_skills(skills_root: Path) -> int:
    """Write all paper-agent skill directories under *skills_root*.

    Returns the number of skill directories written.
    """
    router_dir = skills_root / "paper-agent"
    router_dir.mkdir(parents=True, exist_ok=True)
    (router_dir / "SKILL.md").write_text(ROUTER_SKILL)

    count = 1
    for skill_name, skill_content in WORKFLOW_SKILLS.items():
        skill_dir = skills_root / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(skill_content)

        template = SKILL_TEMPLATES.get(skill_name)
        if template:
            ref_dir = skill_dir / "references"
            ref_dir.mkdir(parents=True, exist_ok=True)
            filename = TEMPLATE_FILENAMES[skill_name]
            (ref_dir / filename).write_text(template)
        count += 1

    return count


def _setup_cursor_project(target: Path, cmd: str, args: list[str]) -> None:
    cursor_dir = target / ".cursor"

    mcp_path = cursor_dir / "mcp.json"
    _merge_mcp_json(mcp_path, cmd, args)
    print_success(f"MCP → {mcp_path}")

    skills_root = cursor_dir / "skills"
    n = _write_cursor_skills(skills_root)
    print_success(f"Skills → {skills_root}  ({n} skill directories)")

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

    skills_root = cursor_home / "skills"
    n = _write_cursor_skills(skills_root)
    print_success(f"Skills → {skills_root}  ({n} skill directories)")

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
    cmd_names = ", ".join(f"/{n.removesuffix('.md')}" for n in _CLAUDE_COMMANDS)
    print_success(f"Commands → {commands_dir}  ({cmd_names})")

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

_CURSOR_SKILL = ROUTER_SKILL  # re-exported for _CURSOR_RULE reference

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

_ANALYSIS_TEMPLATE = ""  # templates now live in _skill_content.py

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
- `paper_search_online(query, sources=["arxiv","s2"])` — search arXiv + Semantic Scholar online
- `paper_survey_collect(keywords, venues, years_back)` — collect papers over N years for survey
- `paper_download(paper_ids)` — download PDF files from arXiv
- `paper_export(paper_ids, format)` — export to BibTeX / markdown / JSON
- `paper_find_and_download(title)` — find by exact title and download PDF

### Workspace Layer (v02)
- `paper_workspace_context()` — get workspace context (recent activity, reading progress)
- `paper_workspace_status()` — rebuild and show `.paper-agent/README.md` dashboard
- `paper_reading_status(paper_ids, status)` — set reading status (to_read/reading/read/important)
- `paper_reading_stats()` — reading progress statistics
- `paper_note_add(paper_id, content, note_type)` — save analysis note
- `paper_group_create(name, description)` — create a paper group
- `paper_group_add(name, paper_ids)` — add papers to a group
- `paper_group_list()` — list all groups
- `paper_citations(paper_id, direction, limit)` — query citation relationships

### Profile & Sources Management
- `paper_profile()` — view current research profile
- `paper_profile_update(topics, keywords, enable_sources)` — create/update profile via conversation
- `paper_sources_list()` — list all available sources (arXiv categories, conferences)
- `paper_sources_enable(enable, disable)` — enable/disable specific sources
- `paper_templates_list()` — list research area templates for quick profile setup

## Workflow Skills

paper-agent provides 6 interactive workflow skills. Each skill is a multi-phase
process with interactive checkpoints where the AI MUST ask the user before
proceeding.

| Skill | Trigger | Slash Command |
|-------|---------|--------------|
| **Daily Reading** | "start my day", "每日开工", "今天有什么新论文" | `/start-my-day` |
| **Deep Dive** | "分析这篇论文", arXiv ID, "展开讲讲" | `/paper-analyze` |
| **Literature Survey** | "综述", "survey", "这个方向有哪些工作" | `/paper-survey` |
| **Citation Explore** | "引用链", "谁引用了它", "citations" | `/paper-compare` (citation mode) |
| **Paper Triage** | "帮我筛一下", "哪些值得读", "triage" | `/paper-triage` |
| **Research Insight** | "趋势", "洞察", "什么方法在兴起" | `/paper-insight` |

### Interaction Rules

1. **Always ask at checkpoints**: Each skill has phases with explicit questions.
   Never skip a checkpoint — always present options and wait for user response.
2. **Suggest skill jumps**: At the end of each skill, suggest possible next
   skills (e.g., after deep-dive, offer citation exploration).
3. **Save deliverables**: Each skill ends by offering to save a structured
   deliverable file (daily digest, analysis note, survey, etc.).

## Custom Commands

### Daily Workflow
- `/start-my-day` — daily reading: context recovery → collect → digest → triage
- `/paper-search <query>` — search the library
- `/paper-analyze <paper_id>` — deep analysis with interactive angle selection
- `/paper-collect [days]` — collect from arXiv + DBLP + S2
- `/paper-setup` — guided profile creation through conversation

### Multi-Paper Workflows (v02)
- `/paper-compare` — compare multiple papers side by side
- `/paper-survey <topic>` — generate literature survey with interactive refinement
- `/paper-download <id>` — download PDF files from arXiv
- `/paper-triage` — batch screening: filter → classify → mark reading status
- `/paper-insight <topic>` — trend analysis: method evolution, hot topics, gaps

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
description: "Daily reading workflow: context recovery → collect → digest → triage"
allowed-tools: [
  "mcp__paper-agent__paper_workspace_context",
  "mcp__paper-agent__paper_collect",
  "mcp__paper-agent__paper_digest",
  "mcp__paper-agent__paper_reading_status",
  "mcp__paper-agent__paper_reading_stats",
  "mcp__paper-agent__paper_stats",
  "mcp__paper-agent__paper_note_add"
]
---

# Start My Day — 每日开工

完整的每日研究启动工作流，包含交互式检查点。

## Phase 1: 上下文恢复

1. Call `paper_workspace_context()` to get recent activity
2. Present yesterday's progress summary
3. **ASK THE USER**:
   > 你昨天的进展如上。要：
   > a) 先看昨天未完成的待读论文
   > b) 直接收集今天的新论文
   > c) 两个都要（推荐）

## Phase 2: 采集新论文

1. Call `paper_collect(days=1)` to fetch the latest papers
2. Present source breakdown (arXiv / DBLP / S2)

## Phase 3: 每日推荐

1. Call `paper_digest()` to generate recommendations
2. Present top picks with score and one-line reason
3. **ASK THE USER**:
   > 这 N 篇推荐中，要标记哪些为待读？（编号或"全部"）
   > 有特别重要的吗？我可以标记为"重要"。
4. Call `paper_reading_status(selected_ids, status)` to mark

## Phase 4: 深入（可选）

**ASK THE USER**:
> 要深入看哪篇？还是先干活了？
> - 给我编号 → 切换到 deep-dive 模式
> - "先干活" → 结束

## Phase 5: 交付件

**ASK THE USER**:
> 要保存今天的阅读摘要吗？默认：`daily/{date}.md`
""",
    "paper-search.md": """\
---
description: Search the local paper library by keyword, topic, or method name
argument-hint: <query>
allowed-tools: [
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_show",
  "mcp__paper-agent__paper_search_online",
  "mcp__paper-agent__paper_find_and_download"
]
---

# Paper Search

Search the local paper library.

## Process

1. Parse $ARGUMENTS as the search query
2. Call `paper_search(query=$ARGUMENTS)` to search the library
3. Present results as a concise list — each paper with title, score, and one-line summary
4. If the user asks about a specific paper from the results, call `paper_show(paper_id)` for details
5. If local results are insufficient, suggest online search or find-by-title

## Output Format

找到 N 篇相关论文：

| # | 标题 | 评分 | 摘要 |
|---|------|------|------|
| 1 | ... | 8.5 | ... |

需要查看某篇的详细信息吗？
""",
    "paper-analyze.md": """\
---
description: "Deep dive: structured analysis with interactive angle selection"
argument-hint: <paper_id or arxiv_id>
allowed-tools: [
  "mcp__paper-agent__paper_show",
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_profile",
  "mcp__paper-agent__paper_note_add",
  "mcp__paper-agent__paper_reading_status",
  "mcp__paper-agent__paper_citations",
  "mcp__paper-agent__paper_group_add",
  "mcp__paper-agent__paper_find_and_download",
  "Write"
]
---

# Paper Analyze — 论文深度分析

对单篇论文进行结构化深度分析，保存笔记，管理阅读状态。

## Phase 1: 确认论文

1. Parse $ARGUMENTS as paper_id
2. Call `paper_show(paper_id)` to get details
3. **ASK THE USER**:
   > 要从哪些角度分析？
   > a) 方法创新点  b) 实验设计  c) 与我研究的关联
   > d) 局限与改进空间  e) 全部（推荐首次阅读）

## Phase 2: 生成分析

1. Call `paper_profile()` to get user's research direction
2. Generate analysis using selected angles
3. For angle c), personalize based on user's profile

## Phase 3: 保存与标记

**ASK THE USER**:
> 分析完成。接下来：
> 1. 保存笔记吗？（默认保存到 `.paper-agent/notes/{paper_id}.md`）
> 2. 标记为什么状态？reading / read / important

Call `paper_note_add(paper_id, content, "ai_analysis")` and
`paper_reading_status([paper_id], status)`.

## Phase 4: 延伸（可选）

**ASK THE USER**:
> 要继续做什么？
> a) 查引用链  b) 找相似论文  c) 加入分组  d) 对比  e) 结束
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
  "mcp__paper-agent__paper_group_create",
  "mcp__paper-agent__paper_group_add",
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
description: "Literature survey: interactive keyword refinement → search → draft → iterate"
argument-hint: <topic>
allowed-tools: [
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_search_batch",
  "mcp__paper-agent__paper_search_online",
  "mcp__paper-agent__paper_survey_collect",
  "mcp__paper-agent__paper_batch_show",
  "mcp__paper-agent__paper_compare",
  "mcp__paper-agent__paper_export",
  "mcp__paper-agent__paper_group_create",
  "mcp__paper-agent__paper_group_add",
  "Write"
]
---

# Paper Survey — 文献综述

从需求澄清到综述成文的完整流程，带交互式论文筛选和迭代修改。

## Phase 1: 需求澄清

**ASK THE USER** (依次):
1. 综述的主题是什么？
2. 要覆盖哪些子方向？我帮你拆关键词。
3. 时间范围？a) 1年  b) 3年  c) 5年  d) 自定义
4. 拆分的关键词如下，覆盖够吗？要调整吗？

## Phase 2: 搜索论文

1. `paper_search_batch(queries, diverse=True)` or `paper_survey_collect`
2. **ASK**: 本地结果够吗？要从 arXiv 在线补充吗？
3. If yes: `paper_search_online(query)`

## Phase 3: 论文筛选

Present candidates and **ASK**: 要纳入综述的论文？编号 / "全选" / "前 N 篇"

## Phase 4: 综述生成

**ASK**: 包含哪些章节？关注什么维度？
Generate draft using survey template.

## Phase 5: 迭代

**ASK**: 草稿完成。看看哪里需要修改？

## Phase 6: 交付件

**ASK**: 保存综述？导出 BibTeX？创建论文分组？
""",
    "paper-download.md": """\
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

1. Parse $ARGUMENTS as paper ID(s) or a search query
2. If it looks like a paper ID (e.g., 2301.12345), download directly
3. If it's a title, use `paper_find_and_download(title)` to search and download
4. If it's a query, search first and ask which papers to download
5. Call `paper_download(paper_ids)` to download PDFs
6. Report results in Chinese:
   - ✅ 已下载: filename, path
   - ⏭️ 已存在: filename
   - ❌ 失败: reason
7. Ask: "要阅读哪篇？"
""",
    "paper-triage.md": """\
---
description: "Paper triage: batch screening → classify → mark reading status"
allowed-tools: [
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_digest",
  "mcp__paper-agent__paper_batch_show",
  "mcp__paper-agent__paper_profile",
  "mcp__paper-agent__paper_reading_status",
  "mcp__paper-agent__paper_group_create",
  "mcp__paper-agent__paper_group_add",
  "mcp__paper-agent__paper_group_list",
  "Write"
]
---

# Paper Triage — 论文筛选分流

对一批论文进行快速筛选，按重要程度分流，批量标记状态。

## Phase 1: 确定范围

**ASK THE USER**:
> 要筛选哪些论文？
> a) 今日推荐的论文  b) 某次搜索的结果  c) 某个分组里的论文
> d) 按关键词现搜一批  e) 给我一批 paper ID

## Phase 2: 筛选标准

**ASK THE USER**:
> 按什么标准筛选？
> a) 跟我研究的相关度  b) 方法新颖性  c) 实验质量
> d) 你帮我判断（推荐）  e) 自定义标准
>
> 需要重点关注什么？

## Phase 3: AI 筛选建议

1. Call `paper_profile()` for user's research direction
2. Call `paper_batch_show(paper_ids)` for paper details
3. Classify into: ⭐ 重要 / 📖 待读 / ⏭️ 跳过
4. **ASK**: 同意这个分类吗？要调整哪些？

## Phase 4: 执行操作

1. `paper_reading_status(important_ids, "important")`
2. `paper_reading_status(to_read_ids, "to_read")`
3. **ASK**: 要把"重要"的论文加到某个分组吗？

## Phase 5: 交付件

**ASK**: 要保存筛选报告吗？默认：`triage/{topic}-{date}.md`
""",
    "paper-insight.md": """\
---
description: "Research insight: trend analysis, method evolution, hot topics, gaps"
argument-hint: <topic or research direction>
allowed-tools: [
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_search_batch",
  "mcp__paper-agent__paper_search_online",
  "mcp__paper-agent__paper_batch_show",
  "mcp__paper-agent__paper_profile",
  "mcp__paper-agent__paper_stats",
  "mcp__paper-agent__paper_citations",
  "mcp__paper-agent__paper_reading_status",
  "mcp__paper-agent__paper_group_create",
  "mcp__paper-agent__paper_group_add",
  "Write"
]
---

# Research Insight — 研究趋势洞察

分析某个研究方向的趋势、演进、关键团队和研究空白。

## Phase 1: 洞察范围

**ASK THE USER** (依次):
1. 你想了解哪些方向的趋势？
2. 关注哪些会议/期刊？a) 通用 AI 顶会  b) EDA/硬件  c) 自定义  d) 不限
3. 时间范围？a) 1年  b) 3年（推荐）  c) 5年  d) 自定义
4. 你最关注什么？（可多选）
   a) 方法演进趋势  b) 热门主题变化  c) 关键团队与人物
   d) 研究空白与机会  e) 产业落地情况  f) 全部

## Phase 2: 数据收集

1. `paper_search_batch(queries_by_year_and_direction, diverse=True)`
2. `paper_search_online(query)` if needed
3. **ASK**: 数据够做分析吗？要补充搜索吗？

## Phase 3: 分析与呈现

Generate insight report expanding only user-selected dimensions.

## Phase 4: 深入探索

**ASK THE USER**:
> 洞察报告草稿完成。你想：
> a) 深入看某个趋势  b) 追踪某方法的引用链
> c) 某方向做个综述  d) 修改报告  e) 满意，保存

## Phase 5: 交付件

**ASK**: 保存洞察报告？标记高影响力论文为"待读"？创建分组？
""",
}