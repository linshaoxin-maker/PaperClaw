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

Tools (v01 — single-paper):
  paper_search          Search the local paper library
  paper_show            Show paper details by ID (supports bare arXiv IDs)
  paper_collect         Collect papers from arXiv
  paper_digest          Generate daily digest
  paper_stats           Library statistics
  paper_profile         Current research profile
  paper_profile_update  Create/update profile (topics, keywords, sources)
  paper_sources_list    List all available sources
  paper_sources_enable  Enable/disable sources
  paper_templates_list  List research area templates

Tools (v02 — multi-paper intelligence):
  paper_search_batch    Search multiple topics at once (for surveys / comparisons)
  paper_batch_show      Get details for multiple papers at once
  paper_compare         Structured comparison data for multiple papers
  paper_survey_collect  Collect papers over N years for literature surveys
  paper_export          Export papers to BibTeX / markdown / JSON
  paper_download        Download PDF files from arXiv
  paper_search_online   Search arXiv API in real-time (not just local library)

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
