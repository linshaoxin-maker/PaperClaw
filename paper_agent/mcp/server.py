"""Paper Agent MCP Server entry point.

Starts an MCP server (stdio transport) that exposes paper-agent
tools and resources for consumption by Cursor, Claude Code, etc.
"""

from __future__ import annotations

import sys

from mcp.server.fastmcp import FastMCP

from paper_agent.app.context import AppContext
from paper_agent.mcp.resources import register_resources
from paper_agent.mcp.tools import register_tools

_DESCRIPTION = """\
Paper Agent MCP Server — paper intelligence for AI researchers.

Tools (v01 — core):
  paper_search          Search the local paper library
  paper_show            Show paper details by ID
  paper_collect         Collect papers from all enabled sources
  paper_digest          Generate daily digest
  paper_stats           Library statistics
  paper_profile         Current research profile
  paper_profile_update  Create/update profile
  paper_sources_list    List all available sources
  paper_sources_enable  Enable/disable sources
  paper_templates_list  List research area templates

Tools (v02 — workspace layer):
  paper_workspace_status   Show workspace dashboard (human-readable)
  paper_workspace_context  Get workspace context for session recovery
  paper_reading_status     Set reading status (to_read/reading/read/important)
  paper_reading_stats      Show reading progress statistics
  paper_note_add           Add a note to a paper
  paper_note_show          Show all notes for a paper
  paper_group_create       Create a named paper group
  paper_group_add          Add papers to a group
  paper_group_show         Show papers in a group
  paper_group_list         List all paper groups
  paper_citations          Get citation chain via Semantic Scholar

Tools (v02 — multi-paper intelligence):
  paper_search_batch    Search multiple topics at once
  paper_batch_show      Get details for multiple papers at once
  paper_compare         Structured comparison data
  paper_survey_collect  Collect papers for literature surveys
  paper_export          Export to BibTeX / markdown / JSON
  paper_download        Download PDFs from arXiv
  paper_search_online   Real-time search via arXiv + S2
  paper_find_and_download  Find paper by exact title + download PDF

Tools (v03 — capability-sunk automation):
  paper_quick_scan       One-call topic scan: local + online, deduped, ranked
  paper_auto_triage      Auto-classify papers into important/to_read/skip
  paper_citation_trace   Recursive citation trace (up to 3 levels deep)
  paper_morning_brief    One-call morning pipeline: context + collect + digest
  paper_trend_data       Publication trend data by year × direction

Resources:
  paper://digest/today  Today's digest
  paper://stats         Library stats snapshot
  paper://profile       Research profile
  paper://recent        Recent papers (7 days)
"""


def create_server(config_path: str | None = None) -> FastMCP:
    """Build and return a configured FastMCP server instance."""
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [paper-agent] %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )
    logger = logging.getLogger("paper-agent")

    mcp = FastMCP(
        "paper-agent",
        instructions=_DESCRIPTION,
    )

    # MCP uses stdio for JSON-RPC; logs go to stderr
    ctx = AppContext(config_path, stderr_log=lambda msg: logger.info(msg))
    register_tools(mcp, ctx)
    register_resources(mcp, ctx)

    return mcp


def main() -> None:
    """CLI entry point: ``paper-agent-mcp``."""
    config_path = None
    if "--config" in sys.argv:
        idx = sys.argv.index("--config")
        if idx + 1 < len(sys.argv):
            config_path = sys.argv[idx + 1]

    server = create_server(config_path)
    server.run()


if __name__ == "__main__":
    main()
