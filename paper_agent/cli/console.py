"""Shared Rich console instance and output helpers."""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from paper_agent.domain.models.paper import Paper

console = Console()
err_console = Console(stderr=True)


def print_json_output(data: Any) -> None:
    console.print_json(json.dumps(data, ensure_ascii=False, default=str))


def print_error(message: str) -> None:
    err_console.print(f"[bold red]Error:[/bold red] {message}")


def print_success(message: str) -> None:
    console.print(f"[bold green]{message}[/bold green]")


def print_paper_table(papers: list[Paper], title: str = "Papers") -> None:
    table = Table(title=title, show_lines=True, expand=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Title", ratio=4)
    table.add_column("Score", justify="right", width=6)
    table.add_column("Authors", ratio=2)
    table.add_column("Topics", ratio=2)

    for i, p in enumerate(papers, 1):
        score_style = "bold green" if p.relevance_score >= 7.0 else "yellow" if p.relevance_score >= 4.0 else "dim"
        table.add_row(
            str(i),
            Text(p.title[:80] + ("..." if len(p.title) > 80 else ""), overflow="ellipsis"),
            f"[{score_style}]{p.relevance_score:.1f}[/{score_style}]",
            ", ".join(p.authors[:2]) + ("..." if len(p.authors) > 2 else ""),
            ", ".join(p.topics[:3]),
        )
    console.print(table)


def print_paper_detail(paper: Paper) -> None:
    lines = [
        f"[bold]{paper.title}[/bold]",
        "",
        f"[dim]ID:[/dim] {paper.id}",
        f"[dim]Source:[/dim] {paper.source_name} ({paper.source_paper_id})",
        f"[dim]Authors:[/dim] {', '.join(paper.authors)}",
        f"[dim]Published:[/dim] {paper.published_at.strftime('%Y-%m-%d') if paper.published_at else 'N/A'}",
        f"[dim]URL:[/dim] {paper.url}",
        f"[dim]Score:[/dim] {paper.relevance_score:.1f}/10 ({paper.relevance_band})",
        f"[dim]Topics:[/dim] {', '.join(paper.topics)}",
    ]
    if paper.methodology_tags:
        lines.append(f"[dim]Methods:[/dim] {', '.join(paper.methodology_tags)}")
    if paper.research_objectives:
        lines.append(f"[dim]Objectives:[/dim] {', '.join(paper.research_objectives)}")
    if paper.recommendation_reason:
        lines.append("")
        lines.append(f"[italic]{paper.recommendation_reason}[/italic]")
    lines.append("")
    abstract = paper.abstract if paper.abstract else "(no abstract)"
    lines.append(abstract)

    console.print(Panel("\n".join(lines), title="Paper Detail", border_style="blue"))
