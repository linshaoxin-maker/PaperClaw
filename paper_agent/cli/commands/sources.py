"""paper-agent sources ... commands."""

from __future__ import annotations

from typing import Optional

import typer

from paper_agent.cli.console import print_error, print_json_output, print_success


sources_app = typer.Typer(name="sources", help="Manage paper sources.")


def _get_ctx(config_path: str | None = None):  # type: ignore[no-untyped-def]
    from paper_agent.app.context import AppContext

    return AppContext(config_path)


@sources_app.command("list")
def list_sources(
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """List all known sources (built-in + custom)."""

    ctx = _get_ctx(config_path)
    try:
        ctx.require_initialized()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    sources = ctx.source_registry.list_sources()

    if as_json:
        print_json_output({"status": "ok", "sources": [s.to_dict() for s in sources]})
        return

    for s in sources:
        status = "enabled" if s.enabled else "disabled"
        typer.echo(f"{s.id}\t[{status}]\t{s.display_name}")


@sources_app.command("show")
def show_source(
    source_id: str = typer.Argument(..., help="Source id (e.g. arxiv:cs.AI, conf:neurips)"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Show details for a single source."""

    ctx = _get_ctx(config_path)
    try:
        ctx.require_initialized()
        src = ctx.source_registry.get_source(source_id)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if as_json:
        print_json_output({"status": "ok", "source": src.to_dict()})
        return

    d = src.to_dict()
    for k, v in d.items():
        typer.echo(f"{k}: {v}")


@sources_app.command("enable")
def enable_sources(
    source_ids: list[str] = typer.Argument(..., help="Source id(s) to enable"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Enable one or more sources."""

    ctx = _get_ctx(config_path)
    try:
        ctx.require_initialized()
        ctx.source_registry.enable(source_ids)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    print_success(f"Enabled: {', '.join(source_ids)}")


@sources_app.command("disable")
def disable_sources(
    source_ids: list[str] = typer.Argument(..., help="Source id(s) to disable"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Disable one or more sources."""

    ctx = _get_ctx(config_path)
    try:
        ctx.require_initialized()
        ctx.source_registry.disable(source_ids)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    print_success(f"Disabled: {', '.join(source_ids)}")


@sources_app.command("config")
def sources_config(
    print_only: bool = typer.Option(False, "--print", help="Print user sources override YAML"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Inspect sources override configuration (MVP: print-only)."""

    ctx = _get_ctx(config_path)
    try:
        cfg = ctx.require_initialized()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    user_path = ctx.source_registry.user_sources_path
    payload = {
        "status": "ok",
        "user_sources_path": str(user_path) if user_path else None,
        "hint": "Use 'paper-agent sources enable/disable' to modify enabled state.",
    }

    if as_json:
        print_json_output(payload)
        return

    if print_only:
        if user_path and user_path.exists():
            typer.echo(user_path.read_text())
        else:
            typer.echo("# No user override file yet.")
        return

    typer.echo(f"User sources override file: {payload['user_sources_path']}")
    typer.echo(payload["hint"])
