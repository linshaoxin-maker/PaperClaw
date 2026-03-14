"""Interactive REPL shell for Paper Agent — the default human-facing mode."""

from __future__ import annotations

import shlex
from datetime import date

from rich.table import Table

from paper_agent.cli.console import (
    console,
    print_error,
    print_paper_detail,
    print_paper_table,
    print_success,
)

BANNER = r"""
[bold cyan]  ____                          _                    _
 |  _ \ __ _ _ __   ___ _ __  / \   __ _  ___ _ __ | |_
 | |_) / _` | '_ \ / _ \ '__/ _ \ / _` |/ _ \ '_ \| __|
 |  __/ (_| | |_) |  __/ | / ___ \ (_| |  __/ | | | |_
 |_|   \__,_| .__/ \___|_|/_/   \_\__, |\___|_| |_|\__|
             |_|                   |___/[/bold cyan]
[dim]CLI-first paper intelligence system for AI researchers[/dim]
[dim]Type [bold]help[/bold] for commands, [bold]quit[/bold] to exit[/dim]
"""

HELP_TEXT = """
[bold]Commands:[/bold]

  [cyan]collect[/cyan] [dim][-d DAYS] [-m MAX] [--no-filter][/dim]
      Collect papers from arXiv

  [cyan]digest[/cyan] [dim][--date YYYY-MM-DD][/dim]
      Generate or view the daily digest

  [cyan]search[/cyan] [green]<query>[/green] [dim][-n LIMIT][/dim]
      Search the local paper library

  [cyan]show[/cyan] [green]<id>[/green]
      Show paper detail by ID or row number from last result

  [cyan]stats[/cyan]
      Show library statistics

  [cyan]config[/cyan]
      Show current configuration

  [cyan]help[/cyan]
      Show this help message

  [cyan]quit[/cyan] / [cyan]exit[/cyan] / [cyan]Ctrl+C[/cyan]
      Exit interactive mode
"""


class InteractiveShell:
    def __init__(self, config_path: str | None = None) -> None:
        self._config_path = config_path
        self._ctx: object | None = None
        self._last_results: list = []

    def _get_ctx(self):  # type: ignore[no-untyped-def]
        if self._ctx is None:
            from paper_agent.app.context import AppContext
            self._ctx = AppContext(self._config_path)
        return self._ctx

    def run(self) -> None:
        console.print(BANNER)

        ctx = self._get_ctx()
        if not ctx.config_manager.is_initialized():
            console.print("[yellow]尚未初始化。请先运行 [bold]paper-agent init[/bold] 完成配置。[/yellow]\n")
            return

        cfg = ctx.config
        console.print(f"[dim]Profile: {', '.join(cfg.topics)} | Sources: {', '.join(cfg.sources)}[/dim]")
        total = ctx.storage.count_papers()
        console.print(f"[dim]Library: {total} papers[/dim]\n")

        while True:
            try:
                raw = console.input("[bold green]paper>[/bold green] ").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Bye![/dim]")
                break

            if not raw:
                continue

            try:
                parts = shlex.split(raw)
            except ValueError:
                parts = raw.split()

            cmd = parts[0].lower()
            args = parts[1:]

            try:
                if cmd in ("quit", "exit", "q"):
                    console.print("[dim]Bye![/dim]")
                    break
                elif cmd == "help":
                    console.print(HELP_TEXT)
                elif cmd == "collect":
                    self._cmd_collect(args)
                elif cmd == "digest":
                    self._cmd_digest(args)
                elif cmd in ("search", "s"):
                    self._cmd_search(args)
                elif cmd == "show":
                    self._cmd_show(args)
                elif cmd == "stats":
                    self._cmd_stats()
                elif cmd == "config":
                    self._cmd_config()
                else:
                    # treat entire input as search query
                    self._cmd_search(parts)
            except Exception as e:
                print_error(str(e))

    # ── Commands ──

    def _cmd_collect(self, args: list[str]) -> None:
        ctx = self._get_ctx()
        cfg = ctx.config

        days = 7
        max_results = 200
        do_filter = True

        i = 0
        while i < len(args):
            if args[i] in ("-d", "--days") and i + 1 < len(args):
                days = int(args[i + 1])
                i += 2
            elif args[i] in ("-m", "--max") and i + 1 < len(args):
                max_results = int(args[i + 1])
                i += 2
            elif args[i] == "--no-filter":
                do_filter = False
                i += 1
            else:
                i += 1

        enabled_sources = ctx.source_registry.list_enabled_sources()
        if enabled_sources:
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
        else:
            console.print("[bold green]Collecting papers from arXiv...[/bold green]")
            record = ctx.collection_manager.collect_from_arxiv(
                categories=cfg.sources, days_back=days, max_results=max_results
            )

        if record.status == "failed":
            print_error(f"收集失败: {record.error_summary}")
            return

        print_success(
            f"收集完成: {record.collected_count} 篇 "
            f"({record.new_count} 新增, {record.duplicate_count} 重复)"
        )

        if do_filter and record.new_count > 0:
            console.print("\n[bold]开始 LLM 过滤...[/bold]")
            papers = ctx.storage.get_all_papers(limit=record.collected_count)
            unscored = [p for p in papers if p.lifecycle_state == "discovered"]
            if unscored:
                interests = {"topics": cfg.topics, "keywords": cfg.keywords}
                ctx.filtering_manager.filter_papers(unscored, interests)
                print_success(f"过滤完成: {len(unscored)} 篇论文已评分。")

    def _cmd_digest(self, args: list[str]) -> None:
        ctx = self._get_ctx()
        cfg = ctx.config

        if ctx.storage.count_papers() == 0:
            print_error("本地论文库为空。请先执行 collect。")
            return

        dt = None
        for i, a in enumerate(args):
            if a == "--date" and i + 1 < len(args):
                dt = date.fromisoformat(args[i + 1])

        with console.status("[bold green]Generating digest..."):
            dg = ctx.digest_generator.generate_daily_digest(cfg, target_date=dt)

        console.print(f"\n[bold]Digest — {dg.digest_date.isoformat()}[/bold]")
        console.print(
            f"Library: {dg.stats.total_collected} | "
            f"High: {dg.stats.high_confidence_count} | "
            f"Supplemental: {dg.stats.supplemental_count}"
        )
        if dg.stats.top_topics:
            console.print(f"Topics: {', '.join(dg.stats.top_topics)}")
        console.print()

        all_papers = dg.high_confidence_papers + dg.supplemental_papers
        self._last_results = all_papers

        if dg.high_confidence_papers:
            print_paper_table(dg.high_confidence_papers, title="High Confidence")
        if dg.supplemental_papers:
            print_paper_table(dg.supplemental_papers, title="Supplemental")

        if not all_papers:
            console.print("[yellow]今日无候选论文。[/yellow]")
        elif not dg.high_confidence_papers:
            console.print("[yellow]今日高置信结果较少，已提供补充候选供参考。[/yellow]")

        if dg.artifact_uri:
            console.print(f"\n[dim]Saved: {dg.artifact_uri}[/dim]")

        if all_papers:
            console.print(f"\n[dim]Tip: [bold]show 1[/bold] to view paper #1 detail[/dim]")

    def _cmd_search(self, args: list[str]) -> None:
        if not args:
            print_error("请提供搜索关键词。用法: search <query>")
            return

        ctx = self._get_ctx()
        if ctx.storage.count_papers() == 0:
            print_error("本地论文库为空。请先执行 collect。")
            return

        limit = 20
        diverse = False
        query_parts = []
        i = 0
        while i < len(args):
            if args[i] in ("-n", "--limit") and i + 1 < len(args):
                limit = int(args[i + 1])
                i += 2
            elif args[i] in ("-D", "--diverse"):
                diverse = True
                i += 1
            else:
                query_parts.append(args[i])
                i += 1

        query = " ".join(query_parts)
        result = ctx.search_engine.search(query, limit=limit, diverse=diverse)
        self._last_results = result.papers

        if not result.papers:
            console.print("[yellow]未找到匹配论文。[/yellow]")
        else:
            print_paper_table(result.papers, title=f'Search: "{query}"')
            console.print(f"\n[dim]Tip: [bold]show 1[/bold] to view paper #1 detail[/dim]")

        if result.suggestions:
            console.print()
            for s in result.suggestions:
                if s.type == "diverse_search":
                    console.print(f"[cyan]💡 {s.message}[/cyan]")
                    console.print(f"   → search {query} --diverse")
                elif s.type == "online_search":
                    console.print(f"[cyan]🌐 {s.message}[/cyan]")
                elif s.type == "collect_first":
                    console.print(f"[yellow]📥 {s.message}[/yellow]")

    def _cmd_show(self, args: list[str]) -> None:
        if not args:
            print_error("请提供论文 ID 或结果序号。用法: show <id|#>")
            return

        ctx = self._get_ctx()
        target = args[0]

        # try row number from last results first
        paper = None
        try:
            idx = int(target)
            if 1 <= idx <= len(self._last_results):
                paper = self._last_results[idx - 1]
        except ValueError:
            pass

        if not paper:
            paper = ctx.storage.get_paper(target)
        if not paper:
            paper = ctx.storage.get_paper_by_canonical(target)
        if not paper:
            print_error(f"未找到论文: {target}")
            return

        print_paper_detail(paper)

    def _cmd_stats(self) -> None:
        ctx = self._get_ctx()
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

    def _cmd_config(self) -> None:
        ctx = self._get_ctx()
        cfg = ctx.config
        data = cfg.to_dict()
        console.print("[bold]Current Configuration[/bold]\n")
        for k, v in data.items():
            console.print(f"  [dim]{k}:[/dim] {v}")
