"""MCP resource definitions — expose paper-agent data as readable resources."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date, timedelta

from mcp.server.fastmcp import FastMCP

from paper_agent.app.context import AppContext


def register_resources(mcp: FastMCP, ctx: AppContext) -> None:
    """Register all paper-agent resources on the MCP server instance."""

    @mcp.resource("paper://digest/today")
    def digest_today() -> str:
        """Today's paper digest: high-confidence and supplemental recommendations."""
        cfg = ctx.config
        if ctx.storage.count_papers() == 0:
            return json.dumps({"status": "empty", "message": "Paper library is empty."})
        digest = ctx.digest_generator.generate_daily_digest(cfg)
        return json.dumps(digest.to_dict(), ensure_ascii=False, default=str)

    @mcp.resource("paper://stats")
    def stats_snapshot() -> str:
        """Library statistics snapshot: paper counts and top topics."""
        total = ctx.storage.count_papers()
        papers = ctx.storage.get_all_papers(limit=10000)
        high = sum(1 for p in papers if p.relevance_band == "high")
        low = sum(1 for p in papers if p.relevance_band == "low")
        unscored = sum(1 for p in papers if not p.relevance_band)

        all_topics: list[str] = []
        for p in papers:
            all_topics.extend(p.topics)
        top_topics = [{"topic": t, "count": c} for t, c in Counter(all_topics).most_common(10)]

        return json.dumps({
            "total_papers": total,
            "high_confidence": high,
            "low_confidence": low,
            "unscored": unscored,
            "top_topics": top_topics,
        }, ensure_ascii=False, default=str)

    @mcp.resource("paper://profile")
    def profile_info() -> str:
        """Current research profile: topics, keywords, and enabled sources."""
        cfg = ctx.config
        return json.dumps({
            "topics": cfg.topics,
            "keywords": cfg.keywords,
            "sources": cfg.sources,
            "profile_completed": cfg.profile_completed,
        }, ensure_ascii=False, default=str)

    @mcp.resource("paper://recent")
    def recent_papers() -> str:
        """Papers collected in the last 7 days."""
        since = date.today() - timedelta(days=7)
        papers = ctx.storage.get_papers_by_date(since)
        return json.dumps({
            "count": len(papers),
            "papers": [p.to_summary_dict() for p in papers[:50]],
        }, ensure_ascii=False, default=str)
