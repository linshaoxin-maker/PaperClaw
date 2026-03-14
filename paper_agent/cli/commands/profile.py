"""paper-agent profile ... commands."""

from __future__ import annotations

from typing import Optional

import typer
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from paper_agent.cli.console import console, print_error, print_json_output, print_success


profile_app = typer.Typer(name="profile", help="Manage research profile (topics/keywords) and source recommendations.")


def _get_ctx(config_path: str | None = None):  # type: ignore[no-untyped-def]
    from paper_agent.app.context import AppContext

    return AppContext(config_path)


@profile_app.command("create")
def profile_create(
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Create or update your research profile (guided)."""

    ctx = _get_ctx(config_path)
    try:
        cfg = ctx.require_initialized()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    # Entry selection (MVP: template vs manual)
    entry_completer = WordCompleter(["template", "manual"], ignore_case=True)
    entry = prompt(
        "选择入口 (template/manual): ",
        default="template",
        completer=entry_completer,
    ).strip().lower()

    topics: list[str] = []
    keywords: list[str] = []
    template_id: str | None = None

    if entry == "template":
        templates = ctx.source_registry.list_research_area_templates()
        if not templates:
            print_error("No research area templates found in sources.yaml")
            raise typer.Exit(1)

        template_ids = [t["id"] for t in templates]
        template_completer = WordCompleter(template_ids, ignore_case=True)

        console.print("\n[bold]可用模板：[/bold]")
        for t in templates:
            console.print(f"  - [cyan]{t['id']}[/cyan]: {t.get('name','')}")

        template_id = prompt(
            "选择模板 id: ",
            default=template_ids[0],
            completer=template_completer,
        ).strip()

        t = ctx.source_registry.get_research_area_template(template_id)
        topics = list(t.get("topics", []) or [])
        keywords = list(t.get("keywords", []) or [])

    elif entry == "manual":
        topics_raw = prompt(
            "研究方向 topics (逗号分隔): ",
            default=", ".join(cfg.topics) if cfg.topics else "",
        )
        keywords_raw = prompt(
            "关键词 keywords (逗号分隔): ",
            default=", ".join(cfg.keywords) if cfg.keywords else "",
        )
        topics = [t.strip() for t in topics_raw.split(",") if t.strip()]
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
    else:
        print_error("Invalid entry. Use 'template' or 'manual'.")
        raise typer.Exit(2)

    # Confirm/edit
    console.print("\n[bold]Profile 预览：[/bold]")
    console.print(f"Topics: {topics}")
    console.print(f"Keywords: {keywords}")

    edit = prompt("是否编辑？(y/N): ", default="N").strip().lower() in {"y", "yes"}
    if edit:
        topics_raw = prompt("Topics (逗号分隔): ", default=", ".join(topics))
        keywords_raw = prompt("Keywords (逗号分隔): ", default=", ".join(keywords))
        topics = [t.strip() for t in topics_raw.split(",") if t.strip()]
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

    # Recommend sources from template when available.
    recommended: list[str] = []
    if template_id:
        recommended = ctx.source_registry.recommend_for_template(template_id)

    # Let user choose sources to enable.
    console.print("\n[bold]推荐 sources：[/bold]")
    if recommended:
        for sid in recommended:
            src = ctx.source_registry.get_source(sid)
            console.print(f"  - {sid} ({src.display_name})")
    else:
        console.print("  (无推荐；可后续使用 paper-agent sources enable/disable 调整)")

    enable_default = ", ".join(recommended)
    enable_raw = prompt(
        "启用 sources（逗号分隔，留空表示只保存 topics/keywords）: ",
        default=enable_default,
    )
    enable_sources = [s.strip() for s in enable_raw.split(",") if s.strip()]

    from paper_agent.services.profile_manager import ProfileManager

    pm = ProfileManager(ctx.config_manager, ctx.source_registry)
    try:
        result = pm.apply_profile(topics=topics, keywords=keywords, enable_sources=enable_sources)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if as_json:
        print_json_output({"status": "ok", "profile": result.to_dict()})
        return

    print_success("Profile 已保存。")
    if enable_sources:
        console.print(f"Enabled sources: {', '.join(enable_sources)}")
    console.print("下一步：运行 paper-agent collect")
