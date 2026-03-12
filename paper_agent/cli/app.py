"""Main Typer CLI application for Paper Agent."""

from __future__ import annotations

import json
from datetime import date
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

app = typer.Typer(
    name="paper-agent",
    help="CLI-first paper intelligence system for AI researchers.",
    no_args_is_help=False,
    invoke_without_command=True,
    rich_markup_mode="rich",
)


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
    provider: Optional[str] = typer.Option(None, "--provider", help="LLM provider (anthropic/openai)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="LLM API key"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Custom API base URL"),
    model: Optional[str] = typer.Option(None, "--model", help="LLM model name"),
    topics: Optional[str] = typer.Option(None, "--topics", help="Research topics (comma-separated)"),
    keywords: Optional[str] = typer.Option(None, "--keywords", help="Keywords (comma-separated)"),
    sources: Optional[str] = typer.Option(None, "--sources", help="arXiv categories (comma-separated)"),
) -> None:
    """Initialize Paper Agent with research interests and preferences."""
    from paper_agent.app.config_manager import ConfigManager, ConfigProfile

    cm = ConfigManager(config_path)
    existing_config: ConfigProfile | None = None
    if cm.is_initialized():
        existing_config = cm.load_config()
        if not Confirm.ask("[yellow]配置已存在，是否覆盖？[/yellow]"):
            raise typer.Abort()

    console.print("[bold]Paper Agent 初始化[/bold]\n")

    topics_default = ", ".join(existing_config.topics) if existing_config and existing_config.topics else "retrieval-augmented generation"
    keywords_default = ", ".join(existing_config.keywords) if existing_config else ""
    sources_default = ", ".join(existing_config.sources) if existing_config and existing_config.sources else "cs.AI, cs.LG, cs.CL"
    provider_default = existing_config.llm_provider if existing_config else "anthropic"
    base_url_default = existing_config.llm_base_url if existing_config else ""
    model_default = existing_config.llm_model if existing_config else ""

    # Use prompt_toolkit for better editing experience
    topics_raw = topics if topics is not None else prompt("研究方向 (逗号分隔): ", default=topics_default)
    keywords_raw = keywords if keywords is not None else prompt("关键词 (逗号分隔): ", default=keywords_default)
    sources_raw = sources if sources is not None else prompt("arXiv 分类 (逗号分隔): ", default=sources_default)

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
        # Show masked current key
        masked_key = f"{existing_config.llm_api_key[:8]}...{existing_config.llm_api_key[-4:]}" if len(existing_config.llm_api_key) > 12 else f"{existing_config.llm_api_key[:4]}..."
        console.print(f"当前 API Key: [dim]{masked_key}[/dim]")
        api_key_input = prompt("API Key (留空保持现有配置): ", default="")
        api_key_val = api_key_input or existing_config.llm_api_key
    else:
        api_key_val = prompt("API Key: ")

    base_url_val = base_url if base_url is not None else prompt("Base URL (留空使用默认): ", default=base_url_default)
    model_val = model if model is not None else prompt("Model (留空使用默认): ", default=model_default)

    config = ConfigProfile(
        topics=[t.strip() for t in topics_raw.split(",") if t.strip()],
        keywords=[k.strip() for k in keywords_raw.split(",") if k.strip()],
        sources=[s.strip() for s in sources_raw.split(",") if s.strip()],
        llm_provider=provider_val,
        llm_api_key=api_key_val,
        llm_model=model_val,
        llm_base_url=base_url_val,
    )

    errors = cm.validate_config(config)
    if errors:
        for e in errors:
            print_error(e)
        raise typer.Exit(1)

    cm.ensure_dirs(config)
    cm.save_config(config)

    ctx = _get_ctx(config_path)
    ctx.storage.initialize()

    print_success(f"\n初始化完成！配置已保存到 {cm.config_path}")
    console.print("运行 [bold]paper-agent collect[/bold] 开始收集论文。")


# ── collect ──

@app.command()
def collect(
    days: int = typer.Option(7, "--days", "-d", help="Collect papers from last N days"),
    max_results: int = typer.Option(200, "--max", "-m", help="Max papers per category"),
    do_filter: bool = typer.Option(True, "--filter/--no-filter", help="Run LLM filtering after collection"),
    debug: bool = typer.Option(False, "--debug", help="Show detailed collection logs"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Collect papers from configured arXiv categories."""
    ctx = _get_ctx(config_path, debug=debug)
    try:
        cfg = ctx.require_initialized()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    with console.status("[bold green]Collecting papers from arXiv..."):
        record = ctx.collection_manager.collect_from_arxiv(
            categories=cfg.sources, days_back=days, max_results=max_results
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
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Search the local paper library."""
    ctx = _get_ctx(config_path)
    try:
        ctx.require_initialized()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if ctx.storage.count_papers() == 0:
        print_error("当前本地论文库为空。请先执行 paper-agent collect。")
        raise typer.Exit(1)

    result = ctx.search_engine.search(query, limit=limit)

    if as_json:
        print_json_output(result.to_dict())
        return

    if not result.papers:
        console.print("[yellow]未找到匹配论文。[/yellow]")
        return

    print_paper_table(result.papers, title=f'Search: "{query}"')


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


if __name__ == "__main__":
    app()
