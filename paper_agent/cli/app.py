"""Main Typer CLI application for Paper Agent."""

from __future__ import annotations

import json
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import typer
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from rich.prompt import Confirm

from paper_agent.cli.console import (
    console,
    print_error,
    print_json_output,
    print_paper_detail,
    print_paper_table,
    print_success,
)

from paper_agent.cli.commands.profile import profile_app
from paper_agent.cli.commands.setup import setup_app
from paper_agent.cli.commands.sources import sources_app

app = typer.Typer(
    name="paper-agent",
    help="CLI-first paper intelligence system for AI researchers.",
    no_args_is_help=False,
    invoke_without_command=True,
    rich_markup_mode="rich",
)

app.add_typer(profile_app, name="profile")
app.add_typer(setup_app, name="setup")
app.add_typer(sources_app, name="sources")


@app.callback(invoke_without_command=True)
def _main(
    ctx: typer.Context,
    config_path: Optional[str] = typer.Option(None, "--config", help="Custom config path"),
) -> None:
    """Paper Agent — enter interactive mode when no subcommand is given."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path
    if ctx.invoked_subcommand is None:
        from paper_agent.cli.shell import InteractiveShell
        InteractiveShell(config_path).run()


def _get_ctx(config_path: str | None = None, debug: bool = False):  # type: ignore[no-untyped-def]
    from paper_agent.app.context import AppContext
    return AppContext(config_path, debug=debug)


# ── init ──

@app.command()
def init(
    config_path: Optional[str] = typer.Option(None, "--config", help="Custom config path"),
    local: bool = typer.Option(False, "--local", "-l", help="Initialize in current directory (.paper-agent/)"),
    provider: Optional[str] = typer.Option(None, "--provider", help="LLM provider (anthropic/openai)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="LLM API key"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Custom API base URL"),
    model: Optional[str] = typer.Option(None, "--model", help="LLM model name"),
) -> None:
    """Initialize Paper Agent (LLM-only infrastructure setup).

    By default, uses ~/.paper-agent. Use --local to initialize in cwd/.paper-agent
    so that the paper library is bound to the current project directory.
    """
    from paper_agent.app.config_manager import ConfigManager, ConfigProfile

    if local and not config_path:
        config_path = str(Path.cwd() / ".paper-agent" / "config.yaml")

    cm = ConfigManager(config_path)
    existing_config: ConfigProfile | None = None
    if cm.is_initialized():
        existing_config = cm.load_config()
        if not Confirm.ask("[yellow]配置已存在，是否覆盖？[/yellow]"):
            raise typer.Abort()

    console.print("[bold]Paper Agent 初始化（基础设施）[/bold]\n")

    provider_default = existing_config.llm_provider if existing_config else "anthropic"
    base_url_default = existing_config.llm_base_url if existing_config else ""
    model_default = existing_config.llm_model if existing_config else ""

    # Provider with completion
    provider_completer = WordCompleter(["anthropic", "openai"], ignore_case=True)
    provider_val = provider if provider is not None else prompt(
        "LLM Provider: ",
        default=provider_default,
        completer=provider_completer
    )

    # API Key handling
    if api_key is not None:
        api_key_val = api_key
    elif existing_config and existing_config.llm_api_key:
        masked_key = (
            f"{existing_config.llm_api_key[:8]}...{existing_config.llm_api_key[-4:]}"
            if len(existing_config.llm_api_key) > 12
            else f"{existing_config.llm_api_key[:4]}..."
        )
        console.print(f"当前 API Key: [dim]{masked_key}[/dim]")
        api_key_input = prompt("API Key (留空保持现有配置): ", default="")
        api_key_val = api_key_input or existing_config.llm_api_key
    else:
        api_key_val = prompt("API Key: ")

    base_url_val = base_url if base_url is not None else prompt(
        "Base URL (留空使用默认): ", default=base_url_default
    )
    model_val = model if model is not None else prompt(
        "Model (留空使用默认): ", default=model_default
    )

    config = ConfigProfile(
        llm_provider=provider_val,
        llm_api_key=api_key_val,
        llm_model=model_val,
        llm_base_url=base_url_val,
        profile_completed=False,
    )

    # When --local, override data paths to cwd/.paper-agent
    if local and not existing_config:
        local_dir = Path.cwd() / ".paper-agent"
        config.data_dir = str(local_dir)
        config.db_path = str(local_dir / "library.db")
        config.artifacts_dir = str(local_dir / "artifacts")

    errors = cm.validate_config(config, require_profile=False)
    if errors:
        for e in errors:
            print_error(e)
        raise typer.Exit(1)

    cm.ensure_dirs(config)
    cm.save_config(config)

    ctx = _get_ctx(config_path)
    ctx.storage.initialize()

    print_success(f"\n初始化完成！配置已保存到 {cm.config_path}")
    console.print("下一步：运行 [bold]paper-agent profile create[/bold] 生成研究兴趣与推荐 sources。")


# ── collect ──

@app.command()
def collect(
    days: int = typer.Option(7, "--days", "-d", help="Collect papers from last N days"),
    max_results: int = typer.Option(200, "--max", "-m", help="Max papers per source"),
    do_filter: bool = typer.Option(True, "--filter/--no-filter", help="Run LLM filtering after collection"),
    arxiv_only: bool = typer.Option(False, "--arxiv-only", help="Only collect from arXiv (legacy mode)"),
    debug: bool = typer.Option(False, "--debug", help="Show detailed collection logs"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Collect papers from all enabled sources (arXiv, DBLP, OpenReview, ACL)."""
    ctx = _get_ctx(config_path, debug=debug)
    try:
        cfg = ctx.require_initialized()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if arxiv_only:
        console.print("[bold green]Collecting papers from arXiv...[/bold green]")
        record = ctx.collection_manager.collect_from_arxiv(
            categories=cfg.sources, days_back=days, max_results=max_results
        )
    else:
        enabled_sources = ctx.source_registry.list_enabled_sources()
        if not enabled_sources and not cfg.sources:
            print_error(
                "未配置任何数据源。请先执行 paper-agent profile create "
                "或 paper-agent sources enable <source_id>"
            )
            raise typer.Exit(1)

        source_names = [s.display_name for s in enabled_sources]
        console.print(
            f"[bold green]Collecting from {len(enabled_sources)} sources: "
            f"{', '.join(source_names[:5])}"
            f"{'...' if len(source_names) > 5 else ''}[/bold green]"
        )
        record = ctx.collection_manager.collect_from_sources(
            sources=enabled_sources, profile=cfg,
            days_back=days, max_results=max_results,
        )

    if as_json:
        print_json_output(record.to_dict())
        return

    if record.status == "failed":
        print_error(f"收集失败: {record.error_summary}")
        raise typer.Exit(1)

    print_success(
        f"收集完成: {record.collected_count} 篇论文 "
        f"({record.new_count} 新增, {record.duplicate_count} 重复)"
    )

    if record.error_summary and record.error_summary.get("partial_errors"):
        partial = record.error_summary["partial_errors"]
        console.print(f"[yellow]部分源抓取失败 ({len(partial)}): {list(partial.keys())}[/yellow]")

    if record.collected_count == 0:
        console.print(
            "[yellow]提示: 未获取到任何论文。可使用 [bold]paper-agent collect --debug[/bold] 查看完整抓取日志。[/yellow]"
        )

    if do_filter and record.new_count > 0:
        console.print("\n[bold]开始 LLM 过滤...[/bold]")
        papers = ctx.storage.get_all_papers(limit=record.collected_count)
        unscored = [p for p in papers if p.lifecycle_state == "discovered"]
        if unscored:
            interests = {"topics": cfg.topics, "keywords": cfg.keywords}
            ctx.filtering_manager.filter_papers(unscored, interests)
            print_success(f"过滤完成: {len(unscored)} 篇论文已评分。")


# ── survey ──

@app.command()
def survey(
    keywords: str = typer.Argument(..., help="Research keywords (comma-separated)"),
    years: int = typer.Option(5, "--years", "-y", help="How many years to look back"),
    venues: Optional[str] = typer.Option(None, "--venues", "-v", help="Conference filter (comma-separated, e.g. DAC,ICCAD)"),
    max_results: int = typer.Option(500, "--max", "-m", help="Max total papers"),
    debug: bool = typer.Option(False, "--debug", help="Show detailed logs"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Survey a research topic: collect papers from arXiv + DBLP + Semantic Scholar over N years."""
    ctx = _get_ctx(config_path, debug=debug)
    try:
        ctx.require_initialized()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    venue_list = [v.strip() for v in venues.split(",") if v.strip()] if venues else None

    console.print(
        f"[bold green]Surveying: {', '.join(kw_list)} "
        f"(past {years} years, venues={venue_list or 'all'})[/bold green]"
    )
    record = ctx.collection_manager.survey_topic(
        keywords=kw_list, venues=venue_list,
        years_back=years, max_results=max_results,
    )

    if as_json:
        print_json_output(record.to_dict())
        return

    if record.status == "failed":
        print_error(f"调研失败: {record.error_summary}")
        raise typer.Exit(1)

    print_success(
        f"调研完成: {record.collected_count} 篇论文 "
        f"({record.new_count} 新增, {record.duplicate_count} 重复)"
    )

    if record.error_summary and record.error_summary.get("partial_errors"):
        partial = record.error_summary["partial_errors"]
        console.print(f"[yellow]部分源失败 ({len(partial)}): {list(partial.keys())}[/yellow]")

    console.print(
        f"\n[dim]提示: 使用 [bold]paper-agent search \"{kw_list[0]}\"[/bold] 搜索已入库论文。[/dim]"
    )


# ── digest ──

@app.command()
def digest(
    target_date: Optional[str] = typer.Option(None, "--date", help="Digest date (YYYY-MM-DD)"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Generate or view the daily digest."""
    ctx = _get_ctx(config_path)
    try:
        cfg = ctx.require_initialized()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if ctx.storage.count_papers() == 0:
        print_error("当前本地论文库为空。请先执行 paper-agent collect。")
        raise typer.Exit(1)

    dt = date.fromisoformat(target_date) if target_date else None
    with console.status("[bold green]Generating digest..."):
        dg = ctx.digest_generator.generate_daily_digest(cfg, target_date=dt)

    if as_json:
        print_json_output(dg.to_dict())
        return

    console.print(f"\n[bold]Digest — {dg.digest_date.isoformat()}[/bold]")
    console.print(f"Library: {dg.stats.total_collected} | Filtered: {dg.stats.total_filtered}")
    if dg.stats.top_topics:
        console.print(f"Top topics: {', '.join(dg.stats.top_topics)}")
    console.print()

    if dg.high_confidence_papers:
        print_paper_table(dg.high_confidence_papers, title="High Confidence")

    if dg.supplemental_papers:
        print_paper_table(dg.supplemental_papers, title="Supplemental")

    if not dg.high_confidence_papers and not dg.supplemental_papers:
        console.print("[yellow]今日无候选论文。[/yellow]")
    elif not dg.high_confidence_papers:
        console.print("[yellow]今日高置信结果较少，已提供补充候选供参考。[/yellow]")

    if dg.artifact_uri:
        console.print(f"\nDigest saved: [link]{dg.artifact_uri}[/link]")


# ── search ──

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max results"),
    diverse: bool = typer.Option(
        False, "--diverse", "-D",
        help="Auto-expand keywords (synonyms + profile) for broader results",
    ),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Search the local paper library.

    Use --diverse / -D to auto-expand keywords via synonyms and your
    research profile for broader coverage.
    """
    ctx = _get_ctx(config_path)
    try:
        ctx.require_initialized()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if ctx.storage.count_papers() == 0:
        print_error("当前本地论文库为空。请先执行 paper-agent collect。")
        raise typer.Exit(1)

    result = ctx.search_engine.search(query, limit=limit, diverse=diverse)

    if as_json:
        print_json_output(result.to_dict())
        return

    if not result.papers:
        console.print("[yellow]未找到匹配论文。[/yellow]")
    else:
        print_paper_table(result.papers, title=f'Search: "{query}"')

    if result.suggestions:
        console.print()
        for s in result.suggestions:
            if s.type == "diverse_search":
                console.print(
                    f"[cyan]💡 {s.message}[/cyan]\n"
                    f"   → paper-agent search \"{query}\" --diverse"
                )
            elif s.type == "online_search":
                console.print(
                    f"[cyan]🌐 {s.message}[/cyan]\n"
                    f"   → 通过 MCP 工具 paper_search_online(\"{query}\") 在线搜索"
                )
            elif s.type == "collect_first":
                console.print(
                    f"[yellow]📥 {s.message}[/yellow]\n"
                    f"   → paper-agent collect"
                )


# ── show ──

@app.command()
def show(
    paper_id: str = typer.Argument(..., help="Paper ID to display"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Show detailed information about a paper."""
    ctx = _get_ctx(config_path)
    try:
        ctx.require_initialized()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    paper = ctx.storage.get_paper(paper_id)
    if not paper:
        paper = ctx.storage.get_paper_by_canonical(paper_id)
    if not paper:
        print_error(f"未找到论文: {paper_id}")
        raise typer.Exit(1)

    if as_json:
        print_json_output(paper.to_detail_dict())
        return

    print_paper_detail(paper)


# ── stats ──

@app.command()
def stats(
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Show library statistics."""
    ctx = _get_ctx(config_path)
    try:
        ctx.require_initialized()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    total = ctx.storage.count_papers()
    papers = ctx.storage.get_all_papers(limit=10000)
    high = sum(1 for p in papers if p.relevance_band == "high")
    low = sum(1 for p in papers if p.relevance_band == "low")
    unscored = sum(1 for p in papers if not p.relevance_band)

    from collections import Counter
    all_topics: list[str] = []
    for p in papers:
        all_topics.extend(p.topics)
    top_topics = Counter(all_topics).most_common(10)

    data = {
        "total_papers": total,
        "high_confidence": high,
        "low_confidence": low,
        "unscored": unscored,
        "top_topics": [{"topic": t, "count": c} for t, c in top_topics],
    }

    if as_json:
        print_json_output(data)
        return

    from rich.table import Table

    console.print(f"\n[bold]Library Statistics[/bold]")
    console.print(f"  Total papers:    {total}")
    console.print(f"  High confidence: {high}")
    console.print(f"  Low confidence:  {low}")
    console.print(f"  Unscored:        {unscored}")

    if top_topics:
        table = Table(title="Top Topics")
        table.add_column("Topic")
        table.add_column("Count", justify="right")
        for t, c in top_topics:
            table.add_row(t, str(c))
        console.print(table)


# ── config ──

@app.command(name="config")
def show_config(
    show_secrets: bool = typer.Option(False, "--show-secrets", help="Show full API key (default: masked)"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Show current configuration."""
    ctx = _get_ctx(config_path)
    try:
        cfg = ctx.require_initialized()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    data = cfg.to_dict(mask_api_key=not show_secrets)
    if as_json:
        print_json_output(data)
        return

    console.print("[bold]Current Configuration[/bold]\n")
    for k, v in data.items():
        console.print(f"  [dim]{k}:[/dim] {v}")

    if not show_secrets:
        console.print("\n[dim]提示: 使用 --show-secrets 显示完整 API key[/dim]")


# ── doctor ──

@app.command()
def doctor(
    config_path: Optional[str] = typer.Option(None, "--config", help="Custom config path"),
) -> None:
    """Check that paper-agent is fully set up and ready to use."""
    from rich.table import Table

    checks: list[tuple[str, bool, str]] = []
    cwd = Path.cwd()

    # 1. Config / init
    try:
        from paper_agent.app.config_manager import ConfigManager
        cm = ConfigManager(config_path)
        if cm.is_initialized():
            checks.append(("LLM 配置（paper-agent init）", True, "已初始化"))
        else:
            checks.append(("LLM 配置（paper-agent init）", False, "未初始化 → 运行 paper-agent init"))
    except Exception as e:
        checks.append(("LLM 配置（paper-agent init）", False, str(e)))

    # 2. MCP binary
    mcp_bin = shutil.which("paper-agent-mcp")
    if mcp_bin:
        checks.append(("MCP 可执行文件", True, mcp_bin))
    else:
        venv_bin = Path(sys.executable).parent / "paper-agent-mcp"
        if venv_bin.exists():
            checks.append(("MCP 可执行文件", True, str(venv_bin)))
        else:
            checks.append(("MCP 可执行文件", True, f"{sys.executable} -m paper_agent.mcp (fallback)"))

    # 3. Profile
    try:
        ctx_obj = _get_ctx(config_path)
        cfg = ctx_obj.require_initialized()
        if cfg.topics:
            checks.append(("研究方向（Profile）", True, f"{len(cfg.topics)} topics, {len(cfg.keywords)} keywords"))
        else:
            checks.append(("研究方向（Profile）", False, "未配置 → 运行 paper-agent profile create 或 /paper-setup"))
    except Exception:
        checks.append(("研究方向（Profile）", False, "需要先完成 init"))

    # 4. Library
    try:
        total = ctx_obj.storage.count_papers()
        if total > 0:
            checks.append(("论文库", True, f"{total} 篇论文"))
        else:
            checks.append(("论文库", False, "空 → 运行 paper-agent collect 或 /start-my-day"))
    except Exception:
        checks.append(("论文库", False, "无法连接"))

    # 5. Claude Code config — check project-level first, fall back to global
    claude_home = Path.home() / ".claude"
    claude_project_found = False
    claude_global_found = False

    claude_mcp = cwd / ".mcp.json"
    claude_md = cwd / "CLAUDE.md"
    claude_cmds = cwd / ".claude" / "commands"
    claude_skills = cwd / ".claude" / "skills"
    if claude_mcp.exists() and claude_md.exists():
        parts = ["project"]
        if claude_cmds.exists():
            cmd_count = len(list(claude_cmds.glob("*.md")))
            parts.append(f"{cmd_count} commands")
        if claude_skills.exists():
            skill_count = len(list(claude_skills.glob("*/SKILL.md")))
            parts.append(f"{skill_count} skills")
        checks.append(("Claude Code 集成", True, ", ".join(parts)))
        claude_project_found = True

    if not claude_project_found:
        g_cmds = claude_home / "commands"
        g_skills = claude_home / "skills"
        g_md = claude_home / "CLAUDE.md"
        if g_cmds.exists() or g_skills.exists() or g_md.exists():
            parts = ["global (~/.claude)"]
            if g_cmds.exists():
                cmd_count = len(list(g_cmds.glob("*.md")))
                parts.append(f"{cmd_count} commands")
            if g_skills.exists():
                skill_count = len(list(g_skills.glob("*/SKILL.md")))
                parts.append(f"{skill_count} skills")
            checks.append(("Claude Code 集成", True, ", ".join(parts)))
            claude_global_found = True

    if not claude_project_found and not claude_global_found:
        if claude_mcp.exists():
            checks.append(("Claude Code 集成", False, "缺少 CLAUDE.md → 重新运行 paper-agent setup claude-code"))
        else:
            checks.append(("Claude Code 集成", False, "未配置 → 运行 paper-agent setup claude-code (--scope project 或 global)"))

    # 6. Cursor config — check project-level first, fall back to global
    cursor_home = Path.home() / ".cursor"
    cursor_project_found = False

    cursor_mcp = cwd / ".cursor" / "mcp.json"
    cursor_skills = cwd / ".cursor" / "skills"
    if cursor_mcp.exists():
        parts = ["project"]
        if cursor_skills.exists():
            skill_count = len(list(cursor_skills.glob("*/SKILL.md")))
            parts.append(f"{skill_count} skills")
        checks.append(("Cursor 集成", True, ", ".join(parts)))
        cursor_project_found = True

    if not cursor_project_found:
        g_mcp = cursor_home / "mcp.json"
        g_skills = cursor_home / "skills"
        if g_mcp.exists():
            parts = ["global (~/.cursor)"]
            if g_skills.exists():
                skill_count = len(list(g_skills.glob("*/SKILL.md")))
                parts.append(f"{skill_count} skills")
            checks.append(("Cursor 集成", True, ", ".join(parts)))
        else:
            checks.append(("Cursor 集成", False, "未配置 → 运行 paper-agent setup cursor (--scope project 或 global)"))

    # 7. Workspace
    ws_dir = cwd / ".paper-agent"
    if ws_dir.exists() and (ws_dir / "研究日志.md").exists():
        checks.append(("Workspace（.paper-agent/）", True, str(ws_dir)))
    elif ws_dir.exists():
        checks.append(("Workspace（.paper-agent/）", False, "不完整 → 重新运行 setup"))
    else:
        checks.append(("Workspace（.paper-agent/）", False, "未初始化 → 运行 setup 自动创建"))

    table = Table(title="Paper Agent 健康检查")
    table.add_column("检查项", style="bold")
    table.add_column("状态", width=4)
    table.add_column("详情")

    all_ok = True
    for name, ok, detail in checks:
        status = "[green]✅[/green]" if ok else "[red]❌[/red]"
        if not ok:
            all_ok = False
        table.add_row(name, status, detail)

    console.print(table)

    if all_ok:
        console.print("\n[bold green]一切就绪！[/bold green] 可以开始使用了。")
    else:
        console.print("\n[yellow]有些项目需要修复。按上面的提示操作即可。[/yellow]")


# ── mcp-server ──

@app.command(name="mcp-server")
def mcp_server(
    config_path: Optional[str] = typer.Option(None, "--config", help="Custom config path"),
) -> None:
    """Start the MCP server (stdio transport) for Cursor / Claude Code integration."""
    from paper_agent.mcp.server import create_server

    server = create_server(config_path)
    server.run()


if __name__ == "__main__":
    app()
