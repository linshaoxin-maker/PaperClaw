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


_PA_MARKER_START = "<!-- paper-agent:start -->"
_PA_MARKER_END = "<!-- paper-agent:end -->"


def _merge_claude_md(path: Path, content: str) -> None:
    """Write paper-agent section into CLAUDE.md without clobbering user content.

    - File doesn't exist → create with markers
    - File has markers → replace only the section between them
    - File exists, no markers → append section at the end
    """
    block = f"{_PA_MARKER_START}\n{content}\n{_PA_MARKER_END}\n"

    if not path.exists():
        path.write_text(block)
        return

    existing = path.read_text()
    if _PA_MARKER_START in existing and _PA_MARKER_END in existing:
        start = existing.index(_PA_MARKER_START)
        end = existing.index(_PA_MARKER_END) + len(_PA_MARKER_END)
        # consume trailing newline if present
        if end < len(existing) and existing[end] == "\n":
            end += 1
        path.write_text(existing[:start] + block + existing[end:])
    else:
        separator = "" if existing.endswith("\n") else "\n"
        path.write_text(existing + separator + "\n" + block)


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
    _merge_claude_md(claude_md, _CLAUDE_MD)
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

    claude_home = Path.home() / ".claude"
    claude_home.mkdir(parents=True, exist_ok=True)

    commands_dir = claude_home / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)
    for name, content in _CLAUDE_COMMANDS.items():
        (commands_dir / name).write_text(content)
    print_success(f"Commands → {commands_dir} ({len(_CLAUDE_COMMANDS)} commands)")

    skills_dir = claude_home / "skills"
    count = _write_claude_skills(skills_dir)
    print_success(f"Skills → {skills_dir} ({count} workflow skills)")

    claude_md = claude_home / "CLAUDE.md"
    _merge_claude_md(claude_md, _CLAUDE_MD)
    print_success(f"CLAUDE.md → {claude_md}")

    console.print("\n[bold green]✅ 安装完成！[/bold green]")
    console.print("\n[bold]自检：[/bold]")
    console.print("  [cyan]paper-agent doctor[/cyan]  ← 检查安装是否完整")
    console.print("\n[bold]开始使用：[/bold]")
    console.print("  1. 在任意目录运行 [cyan]claude[/cyan]")
    console.print("  2. 输入 [cyan]/paper[/cyan] 查看所有功能")
    console.print("  3. 或直接说 [cyan]\"帮我找 transformer 相关的论文\"[/cyan]\n")


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

- **对话上下文延续**：如果本轮对话中已经搜到/讨论过论文：
  - 用户明确引用（"根据已有的"、"用刚才的"、"基于这些写综述"）→ 直接用，不要确认，不要重搜
  - 用户说了同主题但没明确引用 → 问一下："刚才找到了 N 篇相关论文，直接用这些？还是再补充搜索？"
  - 用户换了新主题 → 当新搜索处理
  - 没有上下文 → 直接搜，不要多问
- **意图驱动**：用户意图明确时（如"根据已有的写综述"），跳过所有中间步骤直接出结果。只有意图真正模糊时才问确认。候选列表展示、维度选择、参数调整等中间步骤，只在缺少必要信息时才执行。
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

### Diagnostics
- `paper_health()` — in-IDE health check (LLM config, profile, library, workspace)

## Interaction Rules

1. **Context carry-over** (CRITICAL): When the user's request relates to papers already found/discussed in this conversation:
   - **Explicit reference** (e.g. "根据已有的", "用刚才的", "基于这些论文", "帮我把这些写成综述"): Use those papers directly. No confirmation needed. No re-search.
   - **Ambiguous** (e.g. user says "写个 GNN 综述", and there are GNN papers in context): ASK "刚才找到了 N 篇 GNN 相关论文，直接用这些？还是再搜索补充？"
   - **New topic** (e.g. context has GNN papers, user asks about "transformer 综述"): Treat as new search, ignore context.
   - **No context**: Search directly, no extra question.
2. **Intent-driven, not step-driven**: When the user's intent is clear (e.g. "根据已有的内容写综述"), skip all intermediate steps and go straight to results. Only ask clarifying questions when the intent is genuinely ambiguous. Intermediate steps (candidate listing, dimension selection, parameter tuning) are skipped unless the user's request lacks essential info.
3. **Fork-only**: Only ask at genuine decision points (max 2-3 options). Before showing results, at most 2 rounds of clarification; after results, decisions are embedded in the output.
4. **Smart defaults**: Prefer `paper_morning_brief` over 3 separate calls. Prefer `paper_quick_scan` over search+online+merge.
5. **Auto-track, opt-in export**: Workspace operations (`paper_note_add`, `paper_reading_status`, `paper_group_add`) run automatically — these are internal tracking. File creation/export (Write tool) requires user confirmation. Each workflow's final FORK includes a save/export option.
6. **Concise**: Max 3 options per question. Smart default + "或者？"
7. **Persona**: Read `mode` from `paper_workspace_context()`. "workspace" → show progress, auto-mark. "lightweight" → just data.
8. **Chinese** for all analysis and summaries.

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

Note: The user's terminal setup flow is: `paper-agent init` (LLM config) → `paper-agent setup claude-code` (install to project) → start Claude Code. If something seems broken, call `paper_health()` to diagnose within this conversation (no need to leave Claude Code). For deeper terminal-level checks, the user can run `paper-agent doctor`.

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
  "mcp__paper-agent__paper_workspace_context",
  "mcp__paper-agent__paper_morning_brief",
  "mcp__paper-agent__paper_quick_scan",
  "mcp__paper-agent__paper_auto_triage",
  "mcp__paper-agent__paper_search",
  "mcp__paper-agent__paper_show",
  "mcp__paper-agent__paper_citation_trace",
  "mcp__paper-agent__paper_trend_data",
  "mcp__paper-agent__paper_compare",
  "mcp__paper-agent__paper_note_add",
  "mcp__paper-agent__paper_reading_status",
  "mcp__paper-agent__paper_health",
  "Read"
]
---

# Paper Agent

Unified entry point — understand user state, recommend actions, and execute in the same turn.

## Process

1. Silently call `paper_workspace_context()` + `paper_stats()` to understand the current state
2. Based on state, show **top 3 recommended actions** (not the full command list):

   **New user** (no profile):
   > 看起来你是第一次用 Paper Agent！我先帮你设置研究方向，这样才能给你个性化的推荐。
   > 告诉我你的研究领域和关注的方向？

   **Empty library** (profile exists, 0 papers):
   > 研究方向已配好，论文库还是空的。建议：
   > 1. **今日推荐** — 收集并推荐最新论文（`/start-my-day`）
   > 2. **搜索论文** — 搜一个你关注的主题
   > 3. **采集论文** — 批量抓取最近一周的论文

   **Has unread papers** (to_read > 0):
   > 你有 N 篇待读论文。建议：
   > 1. **批量筛选** — 帮你自动分出最值得读的（`/paper-triage`）
   > 2. **今日推荐** — 看看今天有没有新论文
   > 3. **搜索论文** — 找特定方向的论文
   >
   > 输入"查看全部功能"展示完整命令列表。你也可以直接说你想做什么。

   **Returning user** (has reading history):
   > 当前状态：库中 N 篇论文 | 待读 X | 阅读中 Y
   > 建议：
   > 1. **今日推荐** — 看看有没有新论文
   > 2. **继续阅读** — 你有 Y 篇正在读
   > 3. **文献综述** / **趋势分析** — 对某个方向做系统梳理
   >
   > 输入"查看全部功能"展示完整命令列表。你也可以直接说你想做什么。

3. **If user says "查看全部功能" or "show all"**, then show the full table:

   | # | 功能 | 说明 | 命令 / 说法 |
   |---|------|------|------------|
   | 1 | 每日推荐 | 收集 + 推荐 | `/start-my-day` 或 "今天看什么" |
   | 2 | 搜索论文 | 关键词搜索 | `/paper-search` 或 "搜一下 X" |
   | 3 | 深度分析 | 单篇分析 | `/paper-analyze` 或 "分析这篇" |
   | 4 | 文献综述 | 方向梳理 | `/paper-survey` 或 "综述" |
   | 5 | 趋势分析 | 热度趋势 | `/paper-insight` 或 "这个方向火不火" |
   | 6 | 批量筛选 | 自动分流 | `/paper-triage` 或 "筛一下" |
   | 7 | 论文对比 | 横向对比 | `/paper-compare` 或 "对比这几篇" |
   | 8 | 下载 PDF | 论文全文 | `/paper-download` 或给 arXiv ID |
   | 9 | 引用追踪 | 引用网络 | "引用链" 或 "谁引了这篇" |
   | 10 | 配置方向 | 设定 profile | `/paper-setup` |
   | 11 | 采集论文 | 批量抓取 | `/paper-collect` |
   | 12 | 健康检查 | 诊断安装 | "检查一下" 或 call `paper_health` |

4. **If user directly states intent** (e.g. "今天看什么", "搜 GNN 的论文"), skip the menu and **execute immediately** using the tools above. This is the key difference from a menu — /paper can route AND execute.
5. For multi-step workflows, read `.claude/skills/<name>/SKILL.md` for the full flow.
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

1. **Resolve paper_id**: If $ARGUMENTS is a paper ID or arXiv ID, use it directly. If the user refers to a paper by index (e.g. "第3篇", "上面那篇"), resolve from papers discussed earlier in this conversation.
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

### Step 1 — Resolve papers

- If $ARGUMENTS contains paper IDs → use them directly
- **Explicit reference** ("对比刚才的", "这几篇对比一下") → use those papers directly
- **Ambiguous** (papers in context, no explicit reference) → ASK "刚才找到的这几篇要对比吗？还是指定其他的？"
- **No context, no IDs** → ask which papers to compare

### Step 2 — Compare

When papers are clear (from explicit reference or IDs), default to **全部维度** comparison. Don't ask "which dimensions" unless user specifies.

Call `paper_compare(paper_ids, aspects)` and generate tables in Chinese:

| 维度 | 论文A | 论文B | 论文C |
|------|-------|-------|-------|
| 方法 | ... | ... | ... |
| 关键技术 | ... | ... | ... |
| 主要结果 | ... | ... | ... |
| 适用场景 | ... | ... | ... |

**结论与建议**: 明确判断哪种方法在什么场景下最优，给出选型建议

### Step 3 — After results

ASK: "要保存对比表格吗？或者基于这些写 survey？"
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

### Step 1 — Resolve papers

- **Explicit reference** ("根据已有的", "用刚才的", "基于这些写综述"): use those papers directly. Go to Step 2 immediately — no candidate listing, no selection question.
- **Ambiguous** (same topic in context): ASK "刚才找到了 N 篇相关论文，直接用这些？还是再补充搜索？"
- **New search**: Call `paper_quick_scan(topic=$ARGUMENTS, limit=20)`, then show candidates as table and ASK "全部纳入还是选几篇？"

### Step 2 — Generate survey

Generate survey narrative in Chinese with structured tables:
- **方法分类表**: | 类别 | 代表论文 | 核心思路 | 优势 | 局限 |
- **实验对比表**: | 论文 | 数据集 | 指标1 | 指标2 | 亮点 |
- **研究空白与趋势**: open problems, emerging directions
- **结论与建议**: 当前方向的成熟度判断、主流方法对比结论、研究机会在哪里

### Step 3 — After results

**ASK**: "要修改、补充、还是导出？（BibTeX / Markdown / 保存综述）"

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

1. **Context carry-over**:
   - If user explicitly references existing papers ("筛一下刚才的", "帮我筛这些"): triage those directly → `paper_auto_triage(paper_ids=[...])`
   - If papers in context but reference is ambiguous: ASK "要筛选刚才找到的这些论文？还是筛选库里最近的未读论文？"
   - If no context → default to `paper_auto_triage(top_n=5)`
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
2. **Context carry-over**:
   - If user explicitly references existing papers ("根据刚才的", "用这些做趋势分析"): use those papers directly as landscape
   - If papers in context on the same topic but reference is ambiguous: ASK "刚才找到了 N 篇相关论文，基于这些做趋势分析？还是重新搜索？"
   - If no context → call `paper_quick_scan(topic=$ARGUMENTS, limit=20)` directly
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