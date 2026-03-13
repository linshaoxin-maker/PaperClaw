"""MCP tool definitions — expose paper-agent capabilities as callable tools."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from paper_agent.app.context import AppContext
from paper_agent.domain.models.paper import Paper

_ARXIV_ID_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")


def register_tools(mcp: FastMCP, ctx: AppContext) -> None:
    """Register all paper-agent tools on the MCP server instance."""

    def _resolve_paper(paper_id: str) -> Paper | None:
        """Resolve a paper by internal ID, canonical key, or bare arXiv ID."""
        paper = ctx.storage.get_paper(paper_id)
        if paper:
            return paper
        paper = ctx.storage.get_paper_by_canonical(paper_id)
        if paper:
            return paper
        if _ARXIV_ID_RE.match(paper_id):
            return ctx.storage.get_paper_by_canonical(f"arxiv:{paper_id}")
        return None

    def _resolve_papers(paper_ids: list[str]) -> tuple[list[Paper], list[str]]:
        """Resolve multiple paper IDs. Returns (found, not_found_ids)."""
        found: list[Paper] = []
        not_found: list[str] = []
        for pid in paper_ids:
            p = _resolve_paper(pid)
            if p:
                found.append(p)
            else:
                not_found.append(pid)
        return found, not_found

    @mcp.tool()
    def paper_search(query: str, limit: int = 20) -> str:
        """Search the local paper library using full-text search.

        Args:
            query: Search query (supports natural language and keywords).
            limit: Maximum number of results to return (default 20).

        Returns:
            JSON array of matching papers with title, authors, score, and URL.
        """
        result = ctx.search_engine.search(query, limit=limit)
        if not result.papers:
            return json.dumps({
                "status": "empty",
                "message": "No matching papers found.",
                "papers": [],
            })
        return json.dumps({
            "status": "completed",
            "count": len(result.papers),
            "papers": [p.to_summary_dict() for p in result.papers],
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_show(paper_id: str) -> str:
        """Show detailed information about a specific paper.

        Args:
            paper_id: Paper ID — accepts internal ID, canonical key ('arxiv:2301.12345'),
                      or bare arXiv ID ('2301.12345').

        Returns:
            JSON object with full paper details including abstract, scores, and topics.
        """
        paper = _resolve_paper(paper_id)
        if not paper:
            return json.dumps({"error": f"Paper not found: {paper_id}"})
        return json.dumps(paper.to_detail_dict(), ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_collect(days: int = 7, max_results: int = 200, do_filter: bool = True) -> str:
        """Collect papers from configured arXiv categories.

        This fetches recent papers and optionally scores them with the LLM.
        Requires prior setup via 'paper-agent init' and 'paper-agent profile create'.

        Args:
            days: Number of days to look back (default 7).
            max_results: Maximum papers per category (default 200).
            do_filter: Whether to run LLM relevance scoring (default True).

        Returns:
            JSON object with collection statistics.
        """
        cfg = ctx.config
        record = ctx.collection_manager.collect_from_arxiv(
            categories=cfg.sources, days_back=days, max_results=max_results,
        )

        result: dict[str, Any] = {
            "status": record.status,
            "collected": record.collected_count,
            "new": record.new_count,
            "duplicate": record.duplicate_count,
        }

        if record.status == "failed":
            result["error"] = record.error_summary
            return json.dumps(result, ensure_ascii=False, default=str)

        if do_filter and record.new_count > 0:
            papers = ctx.storage.get_all_papers(limit=record.collected_count)
            unscored = [p for p in papers if p.lifecycle_state == "discovered"]
            if unscored:
                interests = {"topics": cfg.topics, "keywords": cfg.keywords}
                ctx.filtering_manager.filter_papers(unscored, interests)
                result["filtered"] = len(unscored)

        return json.dumps(result, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_digest(target_date: str | None = None) -> str:
        """Generate or retrieve the daily paper digest.

        Args:
            target_date: Date in YYYY-MM-DD format (default: today).

        Returns:
            JSON object with high-confidence and supplemental paper recommendations.
        """
        cfg = ctx.config
        if ctx.storage.count_papers() == 0:
            return json.dumps({"error": "Paper library is empty. Run paper_collect first."})

        dt = date.fromisoformat(target_date) if target_date else None
        digest = ctx.digest_generator.generate_daily_digest(cfg, target_date=dt)
        return json.dumps(digest.to_dict(), ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_stats() -> str:
        """Show library statistics: total papers, confidence distribution, top topics.

        Returns:
            JSON object with library statistics.
        """
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

    @mcp.tool()
    def paper_profile() -> str:
        """Show the current research profile: topics, keywords, enabled sources.

        Returns:
            JSON object with the current research profile configuration.
        """
        cfg = ctx.config
        return json.dumps({
            "topics": cfg.topics,
            "keywords": cfg.keywords,
            "sources": cfg.sources,
            "llm_provider": cfg.llm_provider,
            "llm_model": cfg.llm_model,
            "profile_completed": cfg.profile_completed,
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_profile_update(
        topics: list[str],
        keywords: list[str],
        enable_sources: list[str] | None = None,
    ) -> str:
        """Create or update the research profile through conversation.

        Use this when the user describes their research interests. Extract
        topics and keywords from the conversation, then call this tool.

        Args:
            topics: Research topics, e.g. ["circuit design", "high-level synthesis", "EDA"].
            keywords: Fine-grained keywords, e.g. ["transformer", "GNN", "reinforcement learning"].
            enable_sources: Optional source IDs to enable, e.g. ["arxiv:cs.AI", "arxiv:cs.LG"].
                            If omitted, sources are left unchanged.

        Returns:
            JSON object with the saved profile.
        """
        from paper_agent.services.profile_manager import ProfileManager

        pm = ProfileManager(ctx.config_manager, ctx.source_registry)
        result = pm.apply_profile(
            topics=topics,
            keywords=keywords,
            enable_sources=enable_sources or [],
        )
        # Invalidate cached config so subsequent tools see the update.
        if "config" in ctx.__dict__:
            del ctx.__dict__["config"]
        return json.dumps({
            "status": "ok",
            "profile": result.to_dict(),
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_sources_list() -> str:
        """List all available paper sources with their enabled/disabled status.

        Use this to show the user what sources are available (arXiv categories,
        conferences, etc.) so they can choose which to enable.

        Returns:
            JSON object with all sources grouped by type.
        """
        sources = ctx.source_registry.list_sources()
        grouped: dict[str, list[dict[str, Any]]] = {}
        for s in sources:
            grouped.setdefault(s.type, []).append({
                "id": s.id,
                "name": s.display_name,
                "description": s.description,
                "enabled": s.enabled,
            })
        return json.dumps({
            "total": len(sources),
            "enabled_count": sum(1 for s in sources if s.enabled),
            "sources": grouped,
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_sources_enable(
        enable: list[str] | None = None,
        disable: list[str] | None = None,
    ) -> str:
        """Enable or disable paper sources.

        Args:
            enable: Source IDs to enable, e.g. ["arxiv:cs.AI", "arxiv:cs.LG"].
            disable: Source IDs to disable, e.g. ["arxiv:cs.CV"].

        Returns:
            JSON object with updated enabled sources list.
        """
        if enable:
            ctx.source_registry.enable(enable)
        if disable:
            ctx.source_registry.disable(disable)

        enabled = ctx.source_registry.list_enabled_sources()

        # Sync arXiv categories back to config.
        cfg = ctx.config_manager.load_config()
        arxiv_cats = [
            s.api_config.get("category")
            for s in enabled
            if s.api_type == "arxiv" and s.api_config
        ]
        cfg.sources = [c for c in arxiv_cats if isinstance(c, str) and c]
        ctx.config_manager.save_config(cfg)
        if "config" in ctx.__dict__:
            del ctx.__dict__["config"]

        return json.dumps({
            "status": "ok",
            "enabled_sources": [{"id": s.id, "name": s.display_name} for s in enabled],
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_templates_list() -> str:
        """List available research area templates.

        Templates provide pre-configured topics, keywords, and recommended
        sources for common research areas. Use this to help users quickly
        set up their profile.

        Returns:
            JSON array of templates with id, name, topics, and keywords.
        """
        templates = ctx.source_registry.list_research_area_templates()
        items = []
        for t in templates:
            rec = ctx.source_registry.recommend_for_template(t["id"])
            items.append({
                "id": t["id"],
                "name": t.get("name", ""),
                "topics": t.get("topics", []),
                "keywords": t.get("keywords", []),
                "recommended_sources": rec,
            })
        return json.dumps({"templates": items}, ensure_ascii=False, default=str)

    # ── v02 Tools ──────────────────────────────────────────────────────

    @mcp.tool()
    def paper_batch_show(paper_ids: list[str]) -> str:
        """Get detailed information for multiple papers at once.

        Use this when comparing papers or preparing a survey — fetch all
        papers in one call instead of calling paper_show repeatedly.

        Args:
            paper_ids: List of paper IDs (internal IDs, canonical keys, or bare arXiv IDs).

        Returns:
            JSON object with an array of paper details and any IDs not found.
        """
        found, not_found = _resolve_papers(paper_ids)
        return json.dumps({
            "status": "ok",
            "count": len(found),
            "papers": [p.to_detail_dict() for p in found],
            "not_found": not_found,
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_compare(paper_ids: list[str], aspects: list[str] | None = None) -> str:
        """Provide structured data for comparing multiple papers.

        Returns each paper's metadata organized for side-by-side comparison.
        The AI assistant should use this data to generate comparison tables
        and analysis.

        Args:
            paper_ids: List of paper IDs to compare (2 or more).
            aspects: Optional comparison dimensions. Supported:
                     "method", "result", "application", "architecture".
                     If omitted, all aspects are included.

        Returns:
            JSON object with structured comparison data for each paper.
        """
        if len(paper_ids) < 2:
            return json.dumps({"error": "Need at least 2 papers to compare."})

        found, not_found = _resolve_papers(paper_ids)
        if len(found) < 2:
            return json.dumps({
                "error": f"Found only {len(found)} paper(s). Need at least 2.",
                "not_found": not_found,
            })

        all_aspects = {"method", "result", "application", "architecture"}
        selected = set(aspects) & all_aspects if aspects else all_aspects

        comparison: list[dict[str, Any]] = []
        for p in found:
            entry: dict[str, Any] = {
                "id": p.id,
                "title": p.title,
                "authors": p.authors,
                "published_at": p.published_at.isoformat() if p.published_at else None,
                "url": p.url,
            }
            if "method" in selected:
                entry["method"] = {
                    "methodology_tags": p.methodology_tags,
                    "abstract_excerpt": p.abstract[:500] if p.abstract else "",
                }
            if "result" in selected:
                entry["result"] = {
                    "relevance_score": p.relevance_score,
                    "topics": p.topics,
                }
            if "application" in selected:
                entry["application"] = {
                    "research_objectives": p.research_objectives,
                    "topics": p.topics,
                }
            if "architecture" in selected:
                entry["architecture"] = {
                    "methodology_tags": p.methodology_tags,
                }
            comparison.append(entry)

        return json.dumps({
            "status": "ok",
            "count": len(comparison),
            "aspects": sorted(selected),
            "papers": comparison,
            "not_found": not_found,
            "instruction": (
                "Use this data to generate a comparison table. "
                "Analyze differences in methods, results, and applicability. "
                "Ask the user which dimensions to focus on if not specified."
            ),
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_export(
        paper_ids: list[str],
        format: str = "bibtex",
    ) -> str:
        """Export papers to BibTeX, markdown, or JSON format.

        Args:
            paper_ids: List of paper IDs to export.
            format: Output format — "bibtex", "markdown", or "json".

        Returns:
            JSON object containing the exported content as a string.
        """
        found, not_found = _resolve_papers(paper_ids)
        if not found:
            return json.dumps({"error": "No papers found.", "not_found": not_found})

        if format == "bibtex":
            entries: list[str] = []
            for p in found:
                cite_key = p.source_paper_id.replace(".", "_") if p.source_paper_id else p.id
                author_str = " and ".join(p.authors) if p.authors else "Unknown"
                year = str(p.published_at.year) if p.published_at else ""
                entry = (
                    f"@article{{{cite_key},\n"
                    f"  title   = {{{p.title}}},\n"
                    f"  author  = {{{author_str}}},\n"
                    f"  year    = {{{year}}},\n"
                    f"  url     = {{{p.url}}},\n"
                    f"  note    = {{arXiv:{p.source_paper_id}}}\n"
                    f"}}"
                )
                entries.append(entry)
            content = "\n\n".join(entries)

        elif format == "markdown":
            lines: list[str] = ["# Paper References\n"]
            for i, p in enumerate(found, 1):
                year = str(p.published_at.year) if p.published_at else "N/A"
                authors = ", ".join(p.authors[:3])
                if len(p.authors) > 3:
                    authors += " et al."
                lines.append(f"{i}. **{p.title}**")
                lines.append(f"   - Authors: {authors}")
                lines.append(f"   - Year: {year}")
                lines.append(f"   - URL: {p.url}")
                if p.abstract:
                    lines.append(f"   - Abstract: {p.abstract[:200]}...")
                lines.append("")
            content = "\n".join(lines)

        elif format == "json":
            content = json.dumps(
                [p.to_detail_dict() for p in found],
                ensure_ascii=False, default=str, indent=2,
            )
        else:
            return json.dumps({"error": f"Unsupported format: {format}. Use bibtex, markdown, or json."})

        return json.dumps({
            "status": "ok",
            "format": format,
            "count": len(found),
            "content": content,
            "not_found": not_found,
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_download(
        paper_ids: list[str],
        output_dir: str = "papers",
    ) -> str:
        """Download PDF files for papers from arXiv.

        Args:
            paper_ids: List of paper IDs (internal IDs, canonical keys, or bare arXiv IDs).
            output_dir: Directory to save PDFs (default: 'papers').

        Returns:
            JSON object with download results for each paper.
        """
        import httpx as _httpx

        found, not_found = _resolve_papers(paper_ids)
        if not found:
            return json.dumps({"error": "No papers found.", "not_found": not_found})

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        results: list[dict[str, str]] = []
        client = _httpx.Client(timeout=60.0, follow_redirects=True, trust_env=True)
        try:
            for p in found:
                arxiv_id = p.source_paper_id
                if not arxiv_id and p.canonical_key.startswith("arxiv:"):
                    arxiv_id = p.canonical_key[6:]

                if not arxiv_id:
                    results.append({
                        "id": p.id, "title": p.title,
                        "status": "skipped", "reason": "Not an arXiv paper",
                    })
                    continue

                safe_name = re.sub(r"[^\w\s-]", "", p.title)[:80].strip().replace(" ", "_")
                filename = f"{arxiv_id}_{safe_name}.pdf"
                filepath = out / filename

                if filepath.exists():
                    results.append({
                        "id": p.id, "title": p.title,
                        "status": "exists", "path": str(filepath),
                    })
                    continue

                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                try:
                    resp = client.get(pdf_url)
                    if resp.status_code == 200 and len(resp.content) > 1000:
                        filepath.write_bytes(resp.content)
                        results.append({
                            "id": p.id, "title": p.title,
                            "status": "downloaded", "path": str(filepath),
                        })
                    else:
                        results.append({
                            "id": p.id, "title": p.title,
                            "status": "failed",
                            "reason": f"HTTP {resp.status_code}, size={len(resp.content)}",
                        })
                except Exception as exc:
                    results.append({
                        "id": p.id, "title": p.title,
                        "status": "failed", "reason": str(exc),
                    })
        finally:
            client.close()

        downloaded = sum(1 for r in results if r["status"] == "downloaded")
        existed = sum(1 for r in results if r["status"] == "exists")
        return json.dumps({
            "status": "ok",
            "downloaded": downloaded,
            "already_existed": existed,
            "failed": len(results) - downloaded - existed,
            "results": results,
            "not_found": not_found,
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_search_online(
        query: str,
        max_results: int = 30,
        save_to_library: bool = True,
    ) -> str:
        """Search arXiv online for papers matching a query.

        Unlike paper_search (which searches the local library), this tool
        queries the arXiv API in real-time and can find papers not yet in
        the local library.

        Args:
            query: Search query (natural language or keywords).
            max_results: Maximum number of results (default 30, max 100).
            save_to_library: Whether to save found papers to the local library (default True).

        Returns:
            JSON object with papers found on arXiv.
        """
        from paper_agent.infra.sources.arxiv_adapter import (
            ARXIV_API_URL,
            ArxivAdapter,
        )

        max_results = min(max_results, 100)
        adapter = ArxivAdapter()

        search_query = "+AND+".join(
            f"all:{word}" for word in query.split() if word.strip()
        )
        url = (
            f"{ARXIV_API_URL}?search_query={search_query}"
            f"&start=0&max_results={max_results}"
            f"&sortBy=relevance&sortOrder=descending"
        )

        try:
            import httpx as _httpx
            client = _httpx.Client(timeout=30.0, follow_redirects=True, trust_env=True)
            resp = client.get(url)
            client.close()
            if resp.status_code != 200:
                return json.dumps({
                    "error": f"arXiv API returned {resp.status_code}",
                })
            papers = adapter._parse_response(resp.text)
        except Exception as exc:
            return json.dumps({"error": f"arXiv search failed: {exc}"})

        new_count = 0
        if save_to_library and papers:
            new_count, _ = ctx.storage.save_papers(papers)

        return json.dumps({
            "status": "ok",
            "source": "arxiv_online",
            "count": len(papers),
            "new_saved": new_count,
            "papers": [p.to_summary_dict() for p in papers],
        }, ensure_ascii=False, default=str)
