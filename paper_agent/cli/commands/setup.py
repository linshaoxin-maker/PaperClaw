"""paper-agent setup ... commands — configure IDE integration."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from paper_agent.cli._skill_content import ROUTER_SKILL, WORKFLOW_SKILLS
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

    console.print("\n[bold green]✅ 安装完成！[/bold green]")
    console.print("\n[bold]自检：[/bold]")
    console.print("  [cyan]paper-agent doctor[/cyan]  ← 检查安装是否完整")
    console.print("\n[bold]开始使用：[/bold]")
    console.print("  1. 重启 Cursor（或 Cmd+Shift+P → Reload Window）")
    console.print("  2. 在 Agent chat 中说 [cyan]\"start my day\"[/cyan] 开始使用")
    console.print("  3. 或直接说 [cyan]\"帮我找 transformer 相关论文\"[/cyan]\n")


def _write_cursor_skills(skills_root: Path) -> int:
    """Write the router skill + 6 workflow skills into Cursor's skill dirs."""
    written = 0

    router_dir = skills_root / "paper-agent"
    router_dir.mkdir(parents=True, exist_ok=True)
    (router_dir / "SKILL.md").write_text(ROUTER_SKILL)
    written += 1

    for name, content in WORKFLOW_SKILLS.items():
        skill_dir = skills_root / f"paper-agent-{name}"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(content)
        written += 1

    return written


def _setup_cursor_project(target: Path, cmd: str, args: list[str]) -> None:
    cursor_dir = target / ".cursor"

    mcp_path = cursor_dir / "mcp.json"
    _merge_mcp_json(mcp_path, cmd, args)
    print_success(f"MCP → {mcp_path}")

    skills_root = cursor_dir / "skills"
    count = _write_cursor_skills(skills_root)
    print_success(f"Skills → {skills_root} ({count} skills)")

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
    count = _write_cursor_skills(skills_root)
    print_success(f"Skills → {skills_root} ({count} skills)")

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


def _write_claude_skills(skills_root: Path) -> int:
    """Write the router skill + 6 workflow skills into .claude/skills/ for Claude Code."""
    written = 0

    router_dir = skills_root / "paper-intelligence"
    router_dir.mkdir(parents=True, exist_ok=True)
    (router_dir / "SKILL.md").write_text(ROUTER_SKILL)
    written += 1

    for name, content in WORKFLOW_SKILLS.items():
        skill_dir = skills_root / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(content)
        written += 1

    return written


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
        "(/paper, /start-my-day, /paper-search, /paper-analyze, /paper-collect, "
        "/paper-setup, /paper-compare, /paper-survey, /paper-download, "
        "/paper-triage, /paper-insight)"
    )

    skills_dir = target / ".claude" / "skills"
    count = _write_claude_skills(skills_dir)
    print_success(f"Skills → {skills_dir} ({count} workflow skills)")

    claude_md = target / "CLAUDE.md"
    claude_md.write_text(_CLAUDE_MD)
    print_success(f"CLAUDE.md → {claude_md}")

    _init_workspace(target)

    console.print("\n[bold green]✅ 安装完成！[/bold green]")
    console.print("\n[bold]自检：[/bold]")
    console.print("  [cyan]paper-agent doctor[/cyan]  ← 检查安装是否完整")
    console.print("\n[bold]开始使用：[/bold]")
    console.print(f"  1. 在 [cyan]{target}[/cyan] 目录运行 [cyan]claude[/cyan]")
    console.print("  2. 输入 [cyan]/paper[/cyan] 查看所有功能")
    console.print("  3. 或直接说 [cyan]\"帮我找 transformer 相关的论文\"[/cyan]\n")


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

_CURSOR_SKILL_LEGACY = ""  # Replaced by _write_cursor_skills() using _skill_content.py

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
- 用户说 "start my day" / "今日推荐" / "morning" → `paper_morning_brief(days=1)` 一次调用完成全部

### 搜索
- 搜索关键词 → `paper_search(query)` 或 `paper_quick_scan(topic)` (含在线补充)
- 结果少时自动建议 diverse 搜索或在线搜索

### 单篇分析
- "分析论文" / arXiv ID → `paper_show()` + 生成分析 + `paper_note_add(mark_as="reading")`

### 批量筛选
- "筛一下" / "哪些值得看" / "triage" → `paper_auto_triage()` 自动三档分流

### 引用追踪
- "引用链" / "谁引了" / "citation" → `paper_citation_trace()` 递归追踪

### 趋势分析
- "趋势" / "trend" / "这个方向火不火" → `paper_quick_scan()` + `paper_trend_data()`

### 文献综述
- "综述" / "survey" → `paper_quick_scan()` quick-first 模式

### 对比
- "对比论文" → `paper_batch_show` + `paper_compare`

### 下载
- 给论文标题 → `paper_find_and_download(title)`
- 给 arXiv ID → `paper_download(paper_ids)`

### 分组管理
- 需要建组+加论文 → `paper_group_add(name, ids, create_if_missing=True)` 一步到位

## 行为规范

- 中文输出所有分析和摘要
- fork-only: 只在分叉决策点暂停，最多 2-3 选项；结果之前最多 2 轮确认
- 工作区操作（note_add/reading_status/group_add）自动执行；文件导出需用户在 FORK 中确认
- 论文列表必须用表格展示（| # | 标题 | 评分 | 关键词 | 一句话 |），不要用 bullet list
- 每个 workflow 输出必须以「结论与建议」结尾——告诉用户这些数据意味着什么、下一步该怎么做
- 读取 `paper_workspace_context()` 的 `mode` 字段判断用户类型
- paper-agent 未初始化时引导运行 `paper-agent init`
"""

_ANALYSIS_TEMPLATE_LEGACY = ""  # Replaced by deep-dive skill's inline template

_CLAUDE_MD = """\
# Paper Agent

This project uses **paper-agent** MCP server for research paper intelligence.

## Available MCP Tools

### Core (v01)
- `paper_search(query, diverse=False)` — search local library
- `paper_show(paper_id)` — paper details (accepts arXiv IDs)
- `paper_collect(days)` — collect from arXiv + DBLP + S2
- `paper_digest()` — daily recommendations
- `paper_stats()` — library statistics

### Workspace Layer (v02)
- `paper_workspace_context()` — session recovery (returns `mode: "workspace"|"lightweight"`)
- `paper_workspace_status()` — human-readable dashboard
- `paper_reading_status(paper_ids, status)` — mark as to_read/reading/read/important
- `paper_note_add(paper_id, content, source, mark_as)` — add note + optionally mark status
- `paper_group_create(name)` / `paper_group_add(name, ids, create_if_missing)` — manage groups
- `paper_citations(paper_id, direction)` — single-level citation lookup

### Multi-Paper Intelligence (v02)
- `paper_search_batch(queries)` — multi-topic search
- `paper_batch_show(paper_ids)` — bulk paper details
- `paper_compare(paper_ids, aspects)` — structured comparison
- `paper_search_online(query)` — real-time arXiv + S2
- `paper_survey_collect(keywords, venues, years_back)` — survey collection
- `paper_download(paper_ids)` — PDF download
- `paper_export(paper_ids, format)` — BibTeX/markdown/JSON
- `paper_find_and_download(title)` — find by exact title + download

### Capability-Sunk Automation (v03)
- `paper_quick_scan(topic, limit=20)` — one-call topic scan: local + online, deduped, ranked
- `paper_auto_triage(paper_ids, top_n=5)` — auto-classify into important/to_read/skip
- `paper_citation_trace(paper_id, max_depth=2)` — recursive citation trace in one call
- `paper_morning_brief(days=1)` — one-call morning pipeline: context + collect + digest + auto-mark
- `paper_trend_data(topic, years_back=3)` — publication trend by year x direction

### Profile & Sources
- `paper_profile()` / `paper_profile_update(topics, keywords)` — research profile
- `paper_sources_list()` / `paper_sources_enable(enable, disable)` — source management
- `paper_templates_list()` — research area templates

## Interaction Rules

1. **Fork-only**: Only ask at genuine decision points (max 2-3 options). Before showing results, at most 2 rounds of clarification; after results, decisions are embedded in the output.
2. **Smart defaults**: Prefer `paper_morning_brief` over 3 separate calls. Prefer `paper_quick_scan` over search+online+merge.
3. **Auto-track, opt-in export**: Workspace operations (`paper_note_add`, `paper_reading_status`, `paper_group_add`) run automatically — these are internal tracking. File creation/export (Write tool) requires user confirmation. Each workflow's final FORK includes a save/export option.
4. **Concise**: Max 3 options per question. Smart default + "或者？"
5. **Persona**: Read `mode` from `paper_workspace_context()`. "workspace" → show progress, auto-mark. "lightweight" → just data.
6. **Chinese** for all analysis and summaries.

## Output Format

### Tables First

All paper lists MUST use tables, never bullet-point lists:

| # | 标题 | 评分 | 关键词 | 一句话总结 |
|---|------|------|--------|-----------|

For comparisons, use dimension-based tables:

| 维度 | 论文A | 论文B | 论文C |
|------|-------|-------|-------|

For trends, use year-based tables with direction arrows:

| 子方向 | 2023 | 2024 | 2025 | 趋势 |
|--------|------|------|------|------|

### Conclusion Required

Every workflow output MUST end with a **结论与建议** section BEFORE the FORK options. This section should contain:
- **判断**: What does this data mean? (e.g. "这个方向正在从X转向Y", "论文A的方法在Z场景下明显优于B")
- **建议**: What should the researcher do next? (e.g. "建议优先读第2和第5篇", "如果你关注X，A的方法更适合")

Do NOT just present data — always tell the researcher "so what".

### Format by Workflow

| Workflow | Table format | Conclusion focus |
|----------|-------------|-----------------|
| daily-reading | 评分+关键词+一句话 | 今日最值得关注的方向和论文 |
| search | 评分+关键词+一句话 | 搜索结果中的关键发现 |
| deep-dive | 核心信息表+对比表 | 研究价值判断+与用户研究的关联 |
| compare | 多维对比表 | 哪种方法在什么场景下最优 |
| survey | 方法分类表+实验对比表 | 研究空白和趋势判断 |
| triage | 三档分类表 | 为什么这几篇最重要 |
| insight | 年度趋势表+子方向热度表 | 方向判断和时机建议 |
| citation | 引用树+关键节点表 | 哪些是领域关键节点 |

## First-Run Detection

At session start, silently call `paper_profile()`:
- **No profile**: Say "看起来你还没配置研究方向，我来帮你设置？告诉我你的研究方向就行。" Then guide through profile creation (same flow as /paper-setup). After saving, offer initial collection.
- **Profile exists, empty library** (check `paper_stats()`): Say "研究方向已配好，论文库还是空的。要我帮你采集最近一周的论文吗？"
- **Profile + library exist**: Normal operation. If user seems unsure what to do, suggest `/paper` to see all options.

Note: The user's terminal setup flow is: `paper-agent init` (LLM config) → `paper-agent setup claude-code` (install to project) → start Claude Code. If MCP fails, tell the user to run `paper-agent doctor` in terminal to diagnose.

## Error Handling

- `paper-agent init` not done (MCP connection fails): "paper-agent 还没有初始化。请先在终端运行 `paper-agent init` 配置 LLM。"
- Search returns 0 results: "本地没找到相关论文，要在线搜索吗？" (suggest `paper_search_online`)
- Online search/download fails: "在线搜索暂时不可用，可以先看本地库。" (don't show raw error)
- Empty digest: "今天没有新论文，要搜一个主题看看？" (suggest `paper_quick_scan`)

## Workflow Skills

Detailed workflow definitions live in `.claude/skills/`. When handling a multi-step workflow, read the corresponding SKILL.md:

| Workflow | Skill file | When to read |
|----------|-----------|-------------|
| Daily reading | `.claude/skills/daily-reading/SKILL.md` | /start-my-day or "今天看什么" |
| Deep analysis | `.claude/skills/deep-dive/SKILL.md` | /paper-analyze or "分析这篇" |
| Literature survey | `.claude/skills/literature-survey/SKILL.md` | /paper-survey or "综述" |
| Citation trace | `.claude/skills/citation-explore/SKILL.md` | "引用链" or "谁引了" |
| Paper triage | `.claude/skills/paper-triage/SKILL.md` | /paper-triage or "筛一下" |
| Trend insight | `.claude/skills/research-insight/SKILL.md` | /paper-insight or "趋势" |
| Intent routing | `.claude/skills/paper-intelligence/SKILL.md` | When unsure which workflow to use |

For direct tool calls (morning_brief, auto_triage, citation_trace, quick_scan), no skill file is needed — just call the tool and present results.

## Commands

- `/paper` — **main entry point** (shows what you can do, routes to the right workflow)
- `/start-my-day` — morning brief
- `/paper-search <query>` — search
- `/paper-analyze <id>` — deep analysis
- `/paper-collect [days]` — collect
- `/paper-setup` — profile creation
- `/paper-compare` — compare papers
- `/paper-survey <topic>` — literature survey
- `/paper-download <id>` — download PDF
- `/paper-triage` — batch screening
- `/paper-insight <topic>` — trend analysis
"""

_CLAUDE_COMMANDS: dict[str, str] = {
    "paper.md": """\
---
description: "Paper Agent — unified entry point for all research paper workflows"
allowed-tools: [
  "mcp__paper-agent__paper_profile",
  "mcp__paper-agent__paper_stats",
  "mcp__paper-agent__paper_workspace_context"
]
---

# Paper Agent

Unified entry point — help the researcher decide what to do.

## Process

1. Silently call `paper_workspace_context()` + `paper_stats()` to understand the current state
2. Present a personalized menu based on state:

   **Paper Agent** — 你的研究助手

   当前状态：[库中 N 篇论文 | 待读 X | 阅读中 Y]

   ### Slash 命令

   | # | 功能 | 说明 | 命令 |
   |---|------|------|------|
   | 1 | 每日推荐 | 收集今日论文 + 个性化推荐 | `/start-my-day` |
   | 2 | 搜索论文 | 关键词搜索本地库 | `/paper-search <关键词>` |
   | 3 | 深度分析 | 单篇论文结构化分析 | `/paper-analyze <ID>` |
   | 4 | 文献综述 | 一个方向的论文梳理 | `/paper-survey <主题>` |
   | 5 | 趋势分析 | 研究方向热度和趋势 | `/paper-insight <方向>` |
   | 6 | 批量筛选 | 自动分流待读论文 | `/paper-triage` |
   | 7 | 论文对比 | 多篇论文横向对比 | `/paper-compare` |
   | 8 | 下载 PDF | 下载论文全文 | `/paper-download <ID>` |

   ### 自然语言触发

   不用记命令，直接说需求，我会自动路由到对应的工作流：

   | 你说的话 | 触发的能力 | 背后的 Skill / 工具 |
   |---------|----------|-------------------|
   | "今天看什么" / "start my day" | 每日推荐 | `paper_morning_brief` 一步完成 |
   | "搜一下 GNN placement" | 搜索论文 | `paper_search` / `paper_quick_scan` |
   | "分析这篇" / 给出 arXiv ID | 深度分析 | deep-dive skill |
   | "这个方向有什么工作" / "综述" | 文献综述 | literature-survey skill |
   | "这个方向火不火" / "趋势" | 趋势分析 | research-insight skill |
   | "筛一下" / "哪些值得看" | 批量筛选 | `paper_auto_triage` 一步完成 |
   | "引用链" / "谁引了这篇" | 引用追踪 | `paper_citation_trace` 一步完成 |
   | "帮我找 Attention Is All You Need" | 精确查找 + 下载 | `paper_find_and_download` |
   | "收集论文" / "配置方向" | 采集 / 设置 | `/paper-collect` / `/paper-setup` |

   直接告诉我你想做什么，或输入上面的命令。

3. If user hasn't configured profile yet, skip the menu and guide through setup first
4. If library is empty, suggest starting with `/start-my-day` or `/paper-collect`
5. Route to the selected workflow — for skills, read the corresponding `.claude/skills/<name>/SKILL.md`
""",
    "start-my-day.md": """\
---
description: One-call morning pipeline — context recovery, collect, digest, auto-mark
allowed-tools: [
  "mcp__paper-agent__paper_morning_brief",
  "mcp__paper-agent__paper_show",
  "Read"
]
---

# Start My Day

> Workflow detail: read `.claude/skills/daily-reading/SKILL.md` for full rules, edge cases, and output templates.

Generate today's personalized paper digest in one call.

## Process

1. Call `paper_morning_brief(days=1)` — this single tool does context + collect + digest + auto-mark
2. Present in Chinese with structured format:

   **今日概览**: X 篇新论文，Y 篇高相关

   | # | 标题 | 评分 | 关键词 | 一句话总结 |
   |---|------|------|--------|-----------|

   **结论与建议**: 今日论文主要聚焦于 [方向]，建议优先关注第 X 篇（[理由]）

   If mode is "workspace": mention auto-marked papers
3. **ASK**: "深入看哪篇？保存今日摘要？还是先这样？"
4. If user picks a paper, call `paper_show(paper_id)` for details
5. If user wants to save, write digest to `daily/{YYYY-MM-DD}.md`
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

| # | 标题 | 评分 | 关键词 | 一句话总结 |
|---|------|------|--------|-----------|
| 1 | ... | 8.5 | GNN, placement | ... |

**结论**: [搜索结果中的关键发现，如"这些论文主要分为X和Y两个方向"]

需要查看某篇的详细信息吗？
""",
    "paper-analyze.md": """\
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
5. Generate comparison tables in Chinese:

   **方法对比**:
   | 维度 | 论文A | 论文B | 论文C |
   |------|-------|-------|-------|
   | 方法 | ... | ... | ... |
   | 关键技术 | ... | ... | ... |
   | 主要结果 | ... | ... | ... |
   | 适用场景 | ... | ... | ... |

   **结论与建议**: 明确判断哪种方法在什么场景下最优，给出选型建议
7. Ask: "要保存对比表格吗？或者基于这些写 survey？"
8. If save requested, write to file
9. If export requested, call `paper_export(paper_ids, format="bibtex")`
""",
    "paper-survey.md": """\
---
description: Quick literature survey — one-call topic scan, then optional full survey
argument-hint: <topic>
allowed-tools: [
  "mcp__paper-agent__paper_quick_scan",
  "mcp__paper-agent__paper_batch_show",
  "mcp__paper-agent__paper_compare",
  "mcp__paper-agent__paper_export",
  "mcp__paper-agent__paper_group_add",
  "Read",
  "Write"
]
---

# Paper Survey

> Workflow detail: read `.claude/skills/literature-survey/SKILL.md` for full survey template, quick/full mode rules, and output format.

Quick-first literature survey.

## Process

1. Parse $ARGUMENTS as the survey topic
2. Call `paper_quick_scan(topic=$ARGUMENTS, limit=20)` — local + online, deduped, ranked
3. Present candidates as numbered list with scores
4. **ASK**: "这些是初步候选，要纳入哪些？全部还是选几篇？"
5. For selected papers, generate survey narrative in Chinese
6. **ASK**: "要修改、补充、还是导出？（BibTeX / Markdown / 保存综述）"
7. If user wants to export/save:
   - `paper_export(paper_ids, format="bibtex")` for BibTeX
   - `paper_group_add(name="survey-{topic}", paper_ids, create_if_missing=True)` to group
   - Write survey to `survey/{topic}.md` if saving narrative

Default is quick mode (20 candidates). Full mode (40+) only when user explicitly asks.
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

1. Parse $ARGUMENTS as paper ID(s), title, or a search query
2. If it looks like a paper ID (e.g., 2301.12345), call `paper_download(paper_ids)`
3. If it looks like a paper title, call `paper_find_and_download(title=$ARGUMENTS)`
4. If it's a query, search first and ask which papers to download
5. Report results in Chinese
""",
    "paper-triage.md": """\
---
description: Batch paper screening — auto-classify into important/to_read/skip
allowed-tools: [
  "mcp__paper-agent__paper_auto_triage",
  "mcp__paper-agent__paper_reading_status",
  "Read"
]
---

# Paper Triage

> Workflow detail: read `.claude/skills/paper-triage/SKILL.md` for classification rules, custom source handling, and save report format.

Batch screening of papers using profile-based relevance scores.

## Process

1. Call `paper_auto_triage(top_n=5)` — classifies recent unread papers automatically
2. Present three buckets as tables:

   **⭐ 重要** (N 篇)
   | # | 标题 | 评分 | 入选理由 |
   |---|------|------|---------|

   **📖 待读** (N 篇)
   | # | 标题 | 评分 | 简评 |

   **⏭️ 跳过** (N 篇)
   | # | 标题 | 评分 | 跳过理由 |

   **结论**: 为什么这几篇最值得关注（关联用户 profile 说明）
3. **ASK**: "这是按你 profile 的分类，同意吗？要调整哪些？"
4. Apply status marks per user's confirmation/adjustment
5. **ASK**: "已标记完成。要保存筛选报告？还是先这样？"
""",
    "paper-insight.md": """\
---
description: Research trend analysis — publication trends, sub-direction heat map
argument-hint: <topic>
allowed-tools: [
  "mcp__paper-agent__paper_quick_scan",
  "mcp__paper-agent__paper_trend_data",
  "Read"
]
---

# Research Insight

> Workflow detail: read `.claude/skills/research-insight/SKILL.md` for quick/full mode rules, trend table format, and export options.

Quick trend analysis for a research topic.

## Process

1. Parse $ARGUMENTS as the topic
2. Call `paper_quick_scan(topic=$ARGUMENTS, limit=20)` for recent work
3. Call `paper_trend_data(topic=$ARGUMENTS, years_back=3)` for trend numbers
4. Present as structured tables:

   **趋势总览**
   | 子方向 | 2023 | 2024 | 2025 | 趋势 |
   |--------|------|------|------|------|

   **热门论文**
   | # | 标题 | 年份 | 引用 | 一句话 |
   |---|------|------|------|--------|

   **结论与建议**: 这个方向整体趋势判断，哪些子方向在上升/下降，当前入场的时机建议
5. **ASK**: "要深入某个子方向？导出分析报告？还是先这样？"
""",
}