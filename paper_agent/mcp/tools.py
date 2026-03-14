"""MCP tool definitions — expose paper-agent capabilities as callable tools."""

from __future__ import annotations

import json
import re
import uuid
from collections import Counter
from datetime import date, datetime
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

    def _title_match(query: str, candidate: str) -> bool:
        """Fuzzy title match — case-insensitive, ignores punctuation."""
        def _norm(s: str) -> str:
            return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()
        q, c = _norm(query), _norm(candidate)
        if not q or not c:
            return False
        if q == c:
            return True
        return q in c or c in q

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
    def paper_search(query: str, limit: int = 20, diverse: bool = False) -> str:
        """Search the local paper library using full-text search.

        Args:
            query: Search query (supports natural language and keywords).
            limit: Maximum number of results to return (default 20).
            diverse: If True, auto-expand keywords via synonyms and profile
                     to find more diverse results. Use this when:
                     - The user wants broader coverage
                     - Initial search returned too few results
                     - The query uses abbreviations (e.g. "GNN" → also search
                       "graph neural network")

        Returns:
            JSON object with papers and suggestions. When results are few,
            the 'suggestions' field provides actionable follow-ups:
            - "diverse_search": re-run with diverse=True for keyword expansion
            - "online_search": try paper_search_online for real-time arXiv results
            - "collect_first": local library is empty, run paper_collect first
        """
        result = ctx.search_engine.search(query, limit=limit, diverse=diverse)
        response: dict[str, Any] = {
            "status": result.status,
            "count": len(result.papers),
            "papers": [p.to_summary_dict() for p in result.papers],
        }
        if result.suggestions:
            response["suggestions"] = [
                s.to_dict() if hasattr(s, "to_dict") else s
                for s in result.suggestions
            ]
        if not result.papers:
            response["message"] = "No matching papers found in local library."
        return json.dumps(response, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_search_batch(
        queries: list[str],
        limit_per_query: int = 20,
        diverse: bool = False,
    ) -> str:
        """Search for multiple topics/directions at once. Returns results grouped by query.

        Use this instead of calling paper_search repeatedly when:
        - The user wants to survey multiple research directions
        - The user asks "compare these N topics" or "each direction pick M papers"
        - You need papers from several keyword groups for a literature survey

        Each query is searched independently; a failure in one query does NOT
        affect the others.

        Args:
            queries: List of search queries (one per topic/direction).
            limit_per_query: Max papers to return per query (default 20).
            diverse: If True, auto-expand keywords via synonyms for each query.

        Returns:
            JSON object with results grouped by query, plus aggregate totals.
        """
        groups: list[dict[str, Any]] = []
        total_papers = 0
        for q in queries:
            try:
                result = ctx.search_engine.search(q, limit=limit_per_query, diverse=diverse)
                papers = [p.to_summary_dict() for p in result.papers]
                groups.append({
                    "query": q,
                    "status": result.status,
                    "count": len(papers),
                    "papers": papers,
                })
                total_papers += len(papers)
            except Exception as e:
                groups.append({
                    "query": q,
                    "status": "error",
                    "count": 0,
                    "papers": [],
                    "error": str(e),
                })
        return json.dumps({
            "status": "completed",
            "total_queries": len(queries),
            "total_papers": total_papers,
            "groups": groups,
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
        """Collect papers from all enabled sources (arXiv, DBLP, OpenReview, ACL Anthology).

        Fetches papers concurrently from different API types and optionally
        scores them with the LLM. Requires prior setup via 'paper-agent init'
        and 'paper-agent profile create'.

        Args:
            days: Number of days to look back (default 7).
            max_results: Maximum papers per source (default 200).
            do_filter: Whether to run LLM relevance scoring (default True).

        Returns:
            JSON object with collection statistics.
        """
        enabled_sources = ctx.source_registry.list_enabled_sources()
        if enabled_sources:
            record = ctx.collection_manager.collect_from_sources(
                sources=enabled_sources, profile=ctx.config,
                days_back=days, max_results=max_results,
            )
        else:
            cfg = ctx.config
            record = ctx.collection_manager.collect_from_arxiv(
                categories=cfg.sources, days_back=days, max_results=max_results,
            )

        result: dict[str, Any] = {
            "status": record.status,
            "collected": record.collected_count,
            "new": record.new_count,
            "duplicate": record.duplicate_count,
            "source": record.source_name,
        }

        if record.status == "failed":
            result["error"] = record.error_summary
            return json.dumps(result, ensure_ascii=False, default=str)

        if record.error_summary and record.error_summary.get("partial_errors"):
            result["partial_errors"] = record.error_summary["partial_errors"]

        if do_filter and record.new_count > 0:
            cfg = ctx.config
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

    # ── v02 Workspace Tools ────────────────────────────────────────────

    def _ensure_workspace() -> None:
        """Silently auto-init workspace if not present."""
        ctx.workspace_manager.ensure_initialized()

    @mcp.tool()
    def paper_workspace_status() -> str:
        """Show a human-readable workspace dashboard.

        Returns the current state of the researcher's workspace:
        reading progress, paper groups, recent notes, citation traces,
        and recent activity. Use this to give the user an overview.

        Returns:
            JSON object with workspace status formatted for display.
        """
        _ensure_workspace()
        ctx.workspace_manager.rebuild_dashboard()
        result = ctx.workspace_manager.get_context()
        result["dashboard_file"] = str(ctx.workspace_manager.root / "README.md")
        return json.dumps(result, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_workspace_context() -> str:
        """Get workspace context for session recovery.

        Returns recent journal entries, reading stats, collection list,
        citation traces, and a ``mode`` field indicating the user type:
        - ``"workspace"``: user has reading-list entries or journal activity
        - ``"lightweight"``: workspace is empty or doesn't exist

        Use ``mode`` to decide whether to show workspace features (reading
        progress, groups, status marks) or just present raw results.

        Returns:
            JSON object with mode, journal, reading stats, collections, traces.
        """
        _ensure_workspace()
        result = ctx.workspace_manager.get_context()

        stats = result.get("reading_stats", {})
        journal = result.get("journal_recent", [])
        has_activity = bool(journal) or any(stats.get(k, 0) > 0 for k in ("to_read", "reading", "read", "important"))
        result["mode"] = "workspace" if has_activity else "lightweight"

        return json.dumps(result, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_reading_status(paper_ids: list[str], status: str) -> str:
        """Set the reading status of one or more papers.

        Args:
            paper_ids: List of paper IDs to update.
            status: One of 'to_read', 'reading', 'read', 'important'.

        Returns:
            JSON object with update count, reading stats, and first_use flag.
        """
        _ensure_workspace()
        valid = {"to_read", "reading", "read", "important"}
        if status not in valid:
            return json.dumps({"error": f"Invalid status '{status}'. Use: {sorted(valid)}"})

        existing_stats = ctx.storage.get_reading_stats()
        first_use = sum(existing_stats.values()) == 0

        resolved_ids: list[str] = []
        not_found: list[str] = []
        for pid in paper_ids:
            p = _resolve_paper(pid)
            if p:
                resolved_ids.append(p.id)
            else:
                not_found.append(pid)

        updated = ctx.storage.update_reading_status(resolved_ids, status)
        ctx.workspace_manager.rebuild_reading_list()
        ctx.workspace_manager.append_journal(
            f"标记 {updated} 篇论文为 {status}",
            {"paper_ids": resolved_ids[:5], "status": status},
        )

        stats = ctx.storage.get_reading_stats()
        result: dict[str, Any] = {
            "status": "ok",
            "updated": updated,
            "reading_stats": stats,
            "first_use": first_use,
        }
        if not_found:
            result["not_found"] = not_found
        return json.dumps(result, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_reading_stats() -> str:
        """Show reading progress statistics.

        Returns:
            JSON object with counts per reading status.
        """
        stats = ctx.storage.get_reading_stats()
        papers_by_status: dict[str, list[dict]] = {}
        for s in ("important", "reading", "to_read"):
            papers = ctx.storage.get_papers_by_reading_status(s, limit=10)
            papers_by_status[s] = [
                {"id": p.id, "title": p.title, "score": p.relevance_score}
                for p in papers
            ]
        return json.dumps({
            "stats": stats,
            "recent_by_status": papers_by_status,
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_note_add(paper_id: str, content: str, source: str = "user", mark_as: str | None = None) -> str:
        """Add a note to a paper, optionally setting its reading status.

        Args:
            paper_id: Paper ID (internal, canonical, or arXiv ID).
            content: Note content (markdown supported).
            source: Note source — 'user' for manual notes, 'ai_analysis' for
                    AI-generated analysis.
            mark_as: Optionally set reading status in the same call.
                     One of 'to_read', 'reading', 'read', 'important', or None.

        Returns:
            JSON object with note ID, file path, and first_use flag.
        """
        _ensure_workspace()
        paper = _resolve_paper(paper_id)
        if not paper:
            return json.dumps({"error": f"Paper not found: {paper_id}"})

        notes_dir = ctx.workspace_manager._root / "notes"
        first_use = not notes_dir.exists() or not any(notes_dir.iterdir())

        note_id = uuid.uuid4().hex[:12]
        ctx.storage.save_note(note_id, paper.id, content, source)
        file_path = ctx.workspace_manager.sync_note_file(paper.id)
        ctx.workspace_manager.append_journal(
            f"添加笔记: {paper.title[:60]}",
            {"paper_id": paper.id, "source": source},
        )

        result: dict[str, Any] = {
            "status": "ok",
            "note_id": note_id,
            "paper_id": paper.id,
            "file": str(file_path) if file_path else None,
            "first_use": first_use,
        }

        if mark_as:
            valid = {"to_read", "reading", "read", "important"}
            if mark_as in valid:
                ctx.storage.update_reading_status([paper.id], mark_as)
                ctx.workspace_manager.rebuild_reading_list()
                result["marked_as"] = mark_as
            else:
                result["mark_as_error"] = f"Invalid status '{mark_as}'. Use: {sorted(valid)}"

        return json.dumps(result, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_note_show(paper_id: str) -> str:
        """Show all notes for a paper.

        Args:
            paper_id: Paper ID.

        Returns:
            JSON object with paper info and list of notes.
        """
        paper = _resolve_paper(paper_id)
        if not paper:
            return json.dumps({"error": f"Paper not found: {paper_id}"})

        notes = ctx.storage.get_notes(paper.id)
        return json.dumps({
            "paper_id": paper.id,
            "title": paper.title,
            "notes": notes,
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_group_create(name: str, description: str = "") -> str:
        """Create a named paper group (collection).

        Args:
            name: Group name, e.g. 'rl-placement-papers'.
            description: Optional description of the group's purpose.

        Returns:
            JSON object with group ID and file path.
        """
        _ensure_workspace()
        existing = ctx.storage.get_group(name)
        if existing:
            return json.dumps({"error": f"Group '{name}' already exists.", "id": existing["id"]})

        group_id = uuid.uuid4().hex[:12]
        ctx.storage.create_group(group_id, name, description)
        file_path = ctx.workspace_manager.sync_collection_file(name)
        ctx.workspace_manager.append_journal(
            f"创建分组: {name}",
            {"description": description},
        )
        return json.dumps({
            "status": "ok",
            "id": group_id,
            "name": name,
            "file": str(file_path) if file_path else None,
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_group_add(name: str, paper_ids: list[str], create_if_missing: bool = False) -> str:
        """Add papers to a group, optionally creating it if it doesn't exist.

        Args:
            name: Group name.
            paper_ids: List of paper IDs to add.
            create_if_missing: If True, auto-create the group when it doesn't exist.

        Returns:
            JSON object with add count and group total.
        """
        _ensure_workspace()
        group = ctx.storage.get_group(name)
        if not group:
            if create_if_missing:
                group_id = uuid.uuid4().hex[:12]
                ctx.storage.create_group(group_id, name)
                group = ctx.storage.get_group(name)
            else:
                return json.dumps({"error": f"Group '{name}' not found. Create it first with paper_group_create, or pass create_if_missing=True."})

        resolved_ids: list[str] = []
        not_found: list[str] = []
        for pid in paper_ids:
            p = _resolve_paper(pid)
            if p:
                resolved_ids.append(p.id)
            else:
                not_found.append(pid)

        added = ctx.storage.add_papers_to_group(group["id"], resolved_ids)
        ctx.workspace_manager.sync_collection_file(name)
        ctx.workspace_manager.append_journal(
            f"添加 {added} 篇论文到分组 {name}",
            {"paper_ids": resolved_ids[:5]},
        )

        total_papers = len(ctx.storage.get_group_papers(name))
        result: dict[str, Any] = {
            "status": "ok",
            "added": added,
            "total_in_group": total_papers,
        }
        if not_found:
            result["not_found"] = not_found
        return json.dumps(result, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_group_show(name: str) -> str:
        """Show papers in a group.

        Args:
            name: Group name.

        Returns:
            JSON object with group info and paper list.
        """
        group = ctx.storage.get_group(name)
        if not group:
            return json.dumps({"error": f"Group '{name}' not found."})

        papers = ctx.storage.get_group_papers(name)
        return json.dumps({
            "name": name,
            "description": group.get("description", ""),
            "count": len(papers),
            "papers": [p.to_summary_dict() for p in papers],
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_group_list() -> str:
        """List all paper groups.

        Returns:
            JSON object with list of groups and paper counts.
        """
        groups = ctx.storage.list_groups()
        return json.dumps({
            "count": len(groups),
            "groups": [
                {
                    "name": g["name"],
                    "description": g.get("description", ""),
                    "papers": g.get("paper_count", 0),
                    "updated_at": g.get("updated_at", ""),
                }
                for g in groups
            ],
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_citations(
        paper_id: str,
        direction: str = "both",
        limit: int = 20,
        trace_name: str | None = None,
    ) -> str:
        """Get citation relationships for a paper via Semantic Scholar.

        Queries the S2 API for papers that this paper references (backward)
        and/or papers that cite this paper (forward). New papers found are
        automatically saved to the local library.

        Args:
            paper_id: Paper ID (internal, canonical, or arXiv ID).
            direction: 'references' (backward), 'citations' (forward), or 'both'.
            limit: Max results per direction (default 20).
            trace_name: Optional name for saving a citation trace file.
                        If provided, results are saved to .paper-agent/citation-traces/.

        Returns:
            JSON object with references and/or citations lists.
        """
        paper = _resolve_paper(paper_id)
        if not paper:
            return json.dumps({"error": f"Paper not found: {paper_id}"})

        result = ctx.citation_service.get_citations(paper.id, direction, limit)

        if "error" not in result and trace_name:
            ctx.workspace_manager.update_citation_trace(
                trace_name,
                paper.id,
                paper.title,
                result.get("references", []),
                result.get("citations", []),
            )
            result["trace_file"] = str(
                ctx.workspace_manager.root / "citation-traces" / f"{trace_name}.md"
            )

        ctx.workspace_manager.append_journal(
            f"查询引用: {paper.title[:60]}",
            {
                "direction": direction,
                "references": len(result.get("references", [])),
                "citations": len(result.get("citations", [])),
            },
        )
        return json.dumps(result, ensure_ascii=False, default=str)

    # ── v02 Multi-paper Intelligence ──────────────────────────────────

    @mcp.tool()
    def paper_batch_show(paper_ids: list[str], detail: bool = False) -> str:
        """Get information for multiple papers at once.

        Use this when comparing papers or preparing a survey — fetch all
        papers in one call instead of calling paper_show repeatedly.

        By default returns compact format (truncated abstract, top-5 authors)
        to keep output readable. Set detail=True for full paper data.

        Args:
            paper_ids: List of paper IDs (internal IDs, canonical keys, or bare arXiv IDs).
            detail: If True, return full details (long abstracts, all tags).
                    Default False returns compact format suitable for surveys.

        Returns:
            JSON object with an array of papers and any IDs not found.
        """
        found, not_found = _resolve_papers(paper_ids)
        papers_data = (
            [p.to_detail_dict() for p in found] if detail
            else [p.to_compact_dict() for p in found]
        )
        return json.dumps({
            "status": "ok",
            "count": len(found),
            "papers": papers_data,
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
        """Download PDF files for one or more papers from arXiv.

        Supports batch download — pass multiple IDs to download them all
        at once. Skips papers that are already downloaded.

        Args:
            paper_ids: List of paper IDs to download. Accepts internal IDs,
                       canonical keys ('arxiv:2301.12345'), or bare arXiv IDs.
                       Pass as many IDs as needed for batch download.
            output_dir: Directory to save PDFs (default: 'papers').

        Returns:
            JSON object with per-paper results (downloaded / exists / failed / skipped).
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
    def paper_survey_collect(
        keywords: list[str],
        venues: list[str] | None = None,
        years_back: int = 5,
        max_results: int = 500,
    ) -> str:
        """Survey a research topic by collecting papers from the past N years.

        Searches arXiv + DBLP + Semantic Scholar concurrently for broad
        coverage. Use this when the user wants to understand a research
        direction, prepare a literature review, or explore a new area.

        Args:
            keywords: Research keywords, e.g. ["placement", "EDA", "VLSI"].
            venues: Conference filter, e.g. ["DAC", "ICCAD"]. None = all venues.
            years_back: How many years to look back (default 5).
            max_results: Max total papers to return (default 500).

        Returns:
            JSON object with collection statistics.
        """
        record = ctx.collection_manager.survey_topic(
            keywords=keywords, venues=venues,
            years_back=years_back, max_results=max_results,
        )

        result: dict[str, Any] = {
            "status": record.status,
            "collected": record.collected_count,
            "new": record.new_count,
            "duplicate": record.duplicate_count,
            "source": "survey",
        }
        if record.error_summary:
            result["errors"] = record.error_summary
        return json.dumps(result, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_search_online(
        query: str,
        max_results: int = 30,
        sources: list[str] | None = None,
        save_to_library: bool = True,
    ) -> str:
        """Search online for papers matching a query (arXiv + Semantic Scholar).

        Unlike paper_search (which searches the local library), this tool
        queries external APIs in real-time. By default searches BOTH arXiv
        and Semantic Scholar to cover preprints AND conference/journal papers.

        Args:
            query: Search query (natural language or keywords).
            max_results: Maximum number of results per source (default 30, max 100).
            sources: Which APIs to search. Default ["arxiv", "s2"] (both).
                     Use ["arxiv"] for preprints only, ["s2"] for conferences only.
            save_to_library: Whether to save found papers to the local library (default True).

        Returns:
            JSON object with papers found online, grouped by source.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        if sources is None:
            sources = ["arxiv", "s2"]
        max_results = min(max_results, 100)

        all_papers: list = []
        source_counts: dict[str, int] = {}
        errors: dict[str, str] = {}

        def _search_arxiv() -> list:
            from paper_agent.infra.sources.arxiv_adapter import (
                ARXIV_API_URL,
                ArxivAdapter,
            )
            import httpx as _httpx

            adapter = ArxivAdapter()
            search_query = "+AND+".join(
                f"all:{word}" for word in query.split() if word.strip()
            )
            url = (
                f"{ARXIV_API_URL}?search_query={search_query}"
                f"&start=0&max_results={max_results}"
                f"&sortBy=relevance&sortOrder=descending"
            )
            client = _httpx.Client(timeout=30.0, follow_redirects=True, trust_env=True)
            try:
                resp = client.get(url)
                if resp.status_code != 200:
                    raise RuntimeError(f"arXiv API returned {resp.status_code}")
                return adapter._parse_response(resp.text)
            finally:
                client.close()

        def _search_s2() -> list:
            from paper_agent.infra.sources.semantic_scholar_adapter import (
                SemanticScholarAdapter,
            )
            adapter = SemanticScholarAdapter()
            keywords = [w for w in query.split() if w.strip()]
            return adapter.discover(
                keywords=keywords, max_results=max_results,
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures: dict = {}
            if "arxiv" in sources:
                futures[executor.submit(_search_arxiv)] = "arxiv"
            if "s2" in sources:
                futures[executor.submit(_search_s2)] = "s2"

            for future in as_completed(futures):
                src = futures[future]
                try:
                    papers = future.result()
                    source_counts[src] = len(papers)
                    all_papers.extend(papers)
                except Exception as exc:
                    errors[src] = str(exc)
                    source_counts[src] = 0

        # Deduplicate by canonical_key
        seen: set[str] = set()
        unique: list = []
        for p in all_papers:
            key = p.canonical_key or p.id
            if key not in seen:
                seen.add(key)
                unique.append(p)

        new_count = 0
        if save_to_library and unique:
            new_count, _ = ctx.storage.save_papers(unique)

        result: dict[str, Any] = {
            "status": "ok",
            "sources_searched": list(source_counts.keys()),
            "count": len(unique),
            "new_saved": new_count,
            "per_source": source_counts,
            "papers": [p.to_summary_dict() for p in unique],
        }
        if errors:
            result["errors"] = errors
        return json.dumps(result, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_find_and_download(
        title: str,
        output_dir: str = "papers",
        save_to_library: bool = True,
    ) -> str:
        """Find a paper by its exact title, save it to the library, and download the PDF.

        Searches multiple sources (Semantic Scholar, arXiv) to locate the paper
        by title. This is the go-to tool when the user provides a specific
        paper title and wants you to fetch it.

        The tool:
        1. Searches Semantic Scholar by exact title for broad coverage
        2. Falls back to arXiv title search if S2 misses
        3. Saves the paper to the local library
        4. Downloads the PDF (arXiv or open-access URL)

        Args:
            title: Exact or near-exact paper title, e.g. "Attention Is All You Need".
            output_dir: Directory to save the PDF (default: 'papers').
            save_to_library: Whether to save to local library (default True).

        Returns:
            JSON object with paper metadata and download result.
        """
        import httpx as _httpx
        from paper_agent.domain.models.paper import Paper

        result: dict[str, Any] = {"title_query": title}

        paper_obj: Paper | None = None
        pdf_url: str | None = None

        # --- Strategy 1: Semantic Scholar title search ---
        try:
            client = _httpx.Client(timeout=30.0, follow_redirects=True, trust_env=True)
            s2_url = "https://api.semanticscholar.org/graph/v1/paper/search"
            resp = client.get(
                s2_url,
                params={
                    "query": title,
                    "limit": 5,
                    "fields": "paperId,externalIds,title,authors,abstract,year,url,openAccessPdf,venue",
                },
            )
            client.close()

            if resp.status_code == 200:
                data = resp.json()
                for hit in data.get("data", []):
                    hit_title = (hit.get("title") or "").strip()
                    if _title_match(title, hit_title):
                        ext_ids = hit.get("externalIds") or {}
                        arxiv_id = ext_ids.get("ArXiv")
                        doi = ext_ids.get("DOI")

                        authors = [a.get("name", "") for a in (hit.get("authors") or [])]
                        year = hit.get("year")

                        paper_obj = Paper(
                            id="",
                            canonical_key=f"arxiv:{arxiv_id}" if arxiv_id else f"s2:{hit['paperId']}",
                            source="semantic_scholar",
                            source_paper_id=arxiv_id or hit["paperId"],
                            title=hit_title,
                            authors=authors,
                            abstract=hit.get("abstract") or "",
                            url=hit.get("url") or "",
                            published_at=datetime(year, 1, 1) if year else None,
                        )

                        if arxiv_id:
                            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                        oa = hit.get("openAccessPdf")
                        if oa and oa.get("url"):
                            pdf_url = pdf_url or oa["url"]

                        result["matched_via"] = "semantic_scholar"
                        break
        except Exception as exc:
            result["s2_error"] = str(exc)

        # --- Strategy 2: arXiv title search ---
        if paper_obj is None:
            try:
                from paper_agent.infra.sources.arxiv_adapter import (
                    ARXIV_API_URL,
                    ArxivAdapter,
                )

                adapter = ArxivAdapter()
                encoded = title.replace(" ", "+")
                url = (
                    f"{ARXIV_API_URL}?search_query=ti:%22{encoded}%22"
                    f"&start=0&max_results=5&sortBy=relevance"
                )
                client = _httpx.Client(timeout=30.0, follow_redirects=True, trust_env=True)
                resp = client.get(url)
                client.close()

                if resp.status_code == 200:
                    papers = adapter._parse_response(resp.text)
                    for p in papers:
                        if _title_match(title, p.title):
                            paper_obj = p
                            arxiv_id = p.source_paper_id
                            if arxiv_id:
                                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                            result["matched_via"] = "arxiv"
                            break
            except Exception as exc:
                result["arxiv_error"] = str(exc)

        if paper_obj is None:
            result["status"] = "not_found"
            result["message"] = (
                "Could not find an exact match. Try paper_search_online with keywords."
            )
            return json.dumps(result, ensure_ascii=False, default=str)

        # --- Save to library ---
        if save_to_library:
            new_count, _ = ctx.storage.save_papers([paper_obj])
            saved = ctx.storage.get_paper_by_canonical(paper_obj.canonical_key)
            if saved:
                paper_obj = saved
            result["saved_to_library"] = new_count > 0

        result["paper"] = paper_obj.to_detail_dict()

        # --- Download PDF ---
        if pdf_url:
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)

            safe_name = re.sub(r"[^\w\s-]", "", paper_obj.title)[:80].strip().replace(" ", "_")
            src_id = paper_obj.source_paper_id or paper_obj.id
            filename = f"{src_id}_{safe_name}.pdf"
            filepath = out / filename

            if filepath.exists():
                result["download"] = {"status": "exists", "path": str(filepath)}
            else:
                try:
                    client = _httpx.Client(timeout=60.0, follow_redirects=True, trust_env=True)
                    resp = client.get(pdf_url)
                    client.close()
                    if resp.status_code == 200 and len(resp.content) > 1000:
                        filepath.write_bytes(resp.content)
                        result["download"] = {"status": "downloaded", "path": str(filepath)}
                    else:
                        result["download"] = {
                            "status": "failed",
                            "reason": f"HTTP {resp.status_code}, size={len(resp.content)}",
                            "url": pdf_url,
                        }
                except Exception as exc:
                    result["download"] = {"status": "failed", "reason": str(exc), "url": pdf_url}
        else:
            result["download"] = {
                "status": "no_pdf_url",
                "message": "No arXiv or open-access PDF URL found.",
            }

        result["status"] = "ok"
        return json.dumps(result, ensure_ascii=False, default=str)

    # ── v03: Capability-sunk tools ─────────────────────────────────────

    @mcp.tool()
    def paper_quick_scan(
        topic: str,
        limit: int = 20,
        supplement_online: bool = True,
    ) -> str:
        """Quick-scan a research topic: local search + optional online supplement, deduplicated and ranked.

        Consolidates the multi-step pattern (search_batch → search_online → merge)
        into a single atomic call.  Use for lightweight survey, trend scouting, or
        answering "what work exists on X".

        Args:
            topic: Research topic or question in natural language.
            limit: Maximum papers to return (default 20).
            supplement_online: If True and local results < limit, automatically
                               search arXiv + Semantic Scholar to fill the gap.

        Returns:
            JSON with ranked paper list, source breakdown, and total candidates.
        """
        local_result = ctx.search_engine.search(topic, limit=limit * 2, diverse=True)
        local_papers = local_result.papers

        online_papers: list[Paper] = []
        online_count = 0

        if supplement_online and len(local_papers) < limit:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def _search_arxiv_online() -> list[Paper]:
                from paper_agent.infra.sources.arxiv_adapter import ARXIV_API_URL, ArxivAdapter
                import httpx as _httpx

                adapter = ArxivAdapter()
                search_query = "+AND+".join(f"all:{w}" for w in topic.split() if w.strip())
                url = (
                    f"{ARXIV_API_URL}?search_query={search_query}"
                    f"&start=0&max_results={limit}&sortBy=relevance&sortOrder=descending"
                )
                client = _httpx.Client(timeout=30.0, follow_redirects=True, trust_env=True)
                try:
                    resp = client.get(url)
                    return adapter._parse_response(resp.text) if resp.status_code == 200 else []
                finally:
                    client.close()

            def _search_s2_online() -> list[Paper]:
                from paper_agent.infra.sources.semantic_scholar_adapter import SemanticScholarAdapter
                adapter = SemanticScholarAdapter()
                return adapter.discover(keywords=[w for w in topic.split() if w.strip()], max_results=limit)

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = {executor.submit(_search_arxiv_online): "arxiv", executor.submit(_search_s2_online): "s2"}
                for future in as_completed(futures):
                    try:
                        online_papers.extend(future.result())
                    except Exception:
                        pass
            online_count = len(online_papers)
            if online_papers:
                ctx.storage.save_papers(online_papers)

        seen: set[str] = set()
        merged: list[Paper] = []
        for p in local_papers + online_papers:
            key = p.canonical_key or p.id
            if key not in seen:
                seen.add(key)
                merged.append(p)

        if ctx.search_engine._profile:
            merged = ctx.search_engine.rank_results(merged, topic)
        else:
            merged.sort(key=lambda p: p.relevance_score or 0, reverse=True)

        papers_out = []
        for p in merged[:limit]:
            papers_out.append({
                "id": p.id,
                "title": p.title,
                "authors": p.authors[:3] if p.authors else [],
                "year": p.published_at.year if p.published_at else None,
                "score": round(p.relevance_score, 1) if p.relevance_score else None,
                "source": p.source_name,
                "abstract_snippet": (p.abstract or "")[:200],
            })

        return json.dumps({
            "status": "ok",
            "topic": topic,
            "papers": papers_out,
            "total_candidates": len(merged),
            "local_count": len(local_papers),
            "online_count": online_count,
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_auto_triage(
        paper_ids: list[str] | None = None,
        top_n: int = 5,
        source: str = "recent",
    ) -> str:
        """Automatically classify papers into importance buckets using existing relevance scores.

        No extra LLM calls — uses scores already computed during collection.
        Papers are split into three buckets:
        - important (score >= 8, up to top_n)
        - to_read (score 5–7.9)
        - skip (score < 5)

        Args:
            paper_ids: Specific paper IDs to triage.  If None, triages
                       recent unread papers (last 7 days, no reading status).
            top_n: Max papers in the 'important' bucket (default 5).
            source: When paper_ids is None, which papers to auto-select.
                    'recent' = last 7 days, 'unread' = all without reading status.

        Returns:
            JSON with three buckets, each containing paper summaries with scores and reasons.
        """
        if paper_ids:
            papers, not_found = _resolve_papers(paper_ids)
        else:
            from datetime import datetime, timedelta

            all_papers = ctx.storage.get_all_papers(
                limit=500 if source == "unread" else 200,
            )
            papers = [p for p in all_papers if not p.reading_status]
            if source == "recent":
                cutoff_naive = datetime.utcnow() - timedelta(days=7)
                def _after_cutoff(p):  # noqa: E301
                    if not p.published_at:
                        return False
                    pa = p.published_at.replace(tzinfo=None) if p.published_at.tzinfo else p.published_at
                    return pa >= cutoff_naive
                papers = [p for p in papers if _after_cutoff(p)]
            not_found = []

        important: list[dict[str, Any]] = []
        to_read: list[dict[str, Any]] = []
        skip: list[dict[str, Any]] = []

        for p in papers:
            score = p.relevance_score or 0
            entry = {
                "id": p.id,
                "title": p.title,
                "score": round(score, 1),
                "reason": p.recommendation_reason or "",
                "source": p.source_name,
                "year": p.published_at.year if p.published_at else None,
            }
            if score >= 8:
                important.append(entry)
            elif score >= 5:
                to_read.append(entry)
            else:
                skip.append(entry)

        important.sort(key=lambda x: x["score"], reverse=True)
        to_read.sort(key=lambda x: x["score"], reverse=True)

        result: dict[str, Any] = {
            "status": "ok",
            "important": important[:top_n],
            "to_read": to_read,
            "skip": skip,
            "total": len(papers),
            "summary": f"{len(important[:top_n])} important, {len(to_read)} to_read, {len(skip)} skip",
        }
        if not_found:
            result["not_found"] = not_found
        return json.dumps(result, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_citation_trace(
        paper_id: str,
        direction: str = "both",
        max_depth: int = 2,
        limit_per_level: int = 10,
    ) -> str:
        """Recursively trace citations up to max_depth levels in a single call.

        Replaces the multi-round pattern where the AI calls paper_citations
        repeatedly.  Auto-saves all discovered papers to the local library.

        Args:
            paper_id: Paper ID (internal, canonical, or arXiv ID).
            direction: 'references', 'citations', or 'both' (default).
            max_depth: How many levels deep to trace (default 2, max 3).
            limit_per_level: Max papers to follow per level (default 10).

        Returns:
            JSON with seed paper, tree levels, and discovery stats.
        """
        paper = _resolve_paper(paper_id)
        if not paper:
            return json.dumps({"error": f"Paper not found: {paper_id}"})

        max_depth = min(max_depth, 3)
        result = ctx.citation_service.trace(
            paper.id,
            direction=direction,
            max_depth=max_depth,
            limit_per_level=limit_per_level,
        )

        if "error" not in result:
            trace_name = re.sub(r"[^\w\s-]", "", paper.title)[:50].strip().replace(" ", "-")
            for level in result.get("levels", []):
                refs = [p for p in level.get("papers", []) if p.get("direction") == "reference"]
                cites = [p for p in level.get("papers", []) if p.get("direction") == "cited_by"]
                ctx.workspace_manager.update_citation_trace(
                    trace_name, paper.id, paper.title, refs, cites,
                )
            ctx.workspace_manager.append_journal(
                f"引用追踪: {paper.title[:50]} (depth={max_depth})",
                {"paper_id": paper.id, "total_discovered": result.get("total_discovered", 0)},
            )

        return json.dumps(result, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_morning_brief(days: int = 1) -> str:
        """One-call morning pipeline: context recovery + collect + digest + auto-mark.

        Replaces the 3-step AI chain (workspace_context → collect → digest).
        If the workspace has activity (mode=workspace), top digest picks are
        automatically marked as 'to_read'.

        Args:
            days: How many days back to collect (default 1).

        Returns:
            JSON with workspace context, collection stats, digest, and auto-mark count.
        """
        _ensure_workspace()

        ws_context = ctx.workspace_manager.get_context()
        stats = ws_context.get("reading_stats", {})
        journal = ws_context.get("journal_recent", [])
        has_activity = bool(journal) or any(stats.get(k, 0) > 0 for k in ("to_read", "reading", "read", "important"))
        mode = "workspace" if has_activity else "lightweight"

        # Collect
        enabled_sources = ctx.source_registry.list_enabled_sources()
        if enabled_sources:
            record = ctx.collection_manager.collect_from_sources(
                sources=enabled_sources, profile=ctx.config,
                days_back=days, max_results=200,
            )
        else:
            cfg = ctx.config
            record = ctx.collection_manager.collect_from_arxiv(
                categories=cfg.sources, days_back=days, max_results=200,
            )

        collection_info: dict[str, Any] = {
            "status": record.status,
            "new": record.new_count,
            "duplicate": record.duplicate_count,
        }

        if record.new_count > 0:
            cfg = ctx.config
            all_p = ctx.storage.get_all_papers(limit=record.collected_count)
            unscored = [p for p in all_p if p.lifecycle_state == "discovered"]
            if unscored:
                interests = {"topics": cfg.topics, "keywords": cfg.keywords}
                ctx.filtering_manager.filter_papers(unscored, interests, show_progress=False)

        # Digest
        digest_data: dict[str, Any] = {}
        if ctx.storage.count_papers() > 0:
            digest = ctx.digest_generator.generate_daily_digest(ctx.config)
            digest_data = digest.to_dict()

        # Auto-mark top picks if workspace mode
        auto_marked = 0
        if mode == "workspace" and digest_data.get("high_confidence"):
            top_ids = [p["id"] for p in digest_data["high_confidence"][:5] if p.get("id")]
            if top_ids:
                auto_marked = ctx.storage.update_reading_status(top_ids, "to_read")
                ctx.workspace_manager.rebuild_reading_list()

        ctx.workspace_manager.append_journal(
            f"Morning Brief: {record.new_count} new, {auto_marked} auto-marked",
            {"days": days, "mode": mode},
        )

        return json.dumps({
            "status": "ok",
            "mode": mode,
            "context": ws_context if mode == "workspace" else None,
            "collection": collection_info,
            "digest": digest_data,
            "auto_marked": auto_marked,
        }, ensure_ascii=False, default=str)

    @mcp.tool()
    def paper_trend_data(
        topic: str,
        years_back: int = 3,
    ) -> str:
        """Compute publication trend data for a topic from the local library.

        Groups papers by year and topic tags, computes counts and year-over-year
        deltas.  Replaces "AI mental arithmetic" for trend analysis.

        Args:
            topic: Research topic keywords.
            years_back: How many years to look back (default 3).

        Returns:
            JSON with year-by-year counts per direction, trend indicators,
            and top venues.
        """
        from collections import defaultdict
        from datetime import datetime as dt

        current_year = dt.now().year
        start_year = current_year - years_back

        result = ctx.search_engine.search(topic, limit=1000, diverse=True)
        all_papers = result.papers

        papers_in_range = [
            p for p in all_papers
            if p.published_at and p.published_at.year >= start_year
        ]

        years = list(range(start_year, current_year + 1))

        by_year: dict[int, int] = defaultdict(int)
        by_topic_year: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
        venue_counter: Counter = Counter()

        for p in papers_in_range:
            yr = p.published_at.year
            by_year[yr] += 1
            for t in (p.topics or []):
                by_topic_year[t][yr] += 1
            meta = p.metadata or {}
            venue = meta.get("venue") or p.source_name
            if venue:
                venue_counter[venue] += 1

        def _trend(counts_by_year: dict[int, int]) -> str:
            vals = [counts_by_year.get(y, 0) for y in years]
            if len(vals) < 2:
                return "stable"
            recent = vals[-1]
            prev = vals[-2] if len(vals) >= 2 else 0
            if prev == 0:
                return "up" if recent > 0 else "stable"
            ratio = recent / prev
            if ratio >= 1.5:
                return "up"
            elif ratio <= 0.6:
                return "down"
            return "stable"

        directions = []
        for t in sorted(by_topic_year.keys(), key=lambda k: sum(by_topic_year[k].values()), reverse=True)[:15]:
            counts = [by_topic_year[t].get(y, 0) for y in years]
            directions.append({
                "name": t,
                "counts_by_year": counts,
                "total": sum(counts),
                "trend": _trend(by_topic_year[t]),
            })

        overall_counts = [by_year.get(y, 0) for y in years]

        return json.dumps({
            "status": "ok",
            "topic": topic,
            "years": years,
            "overall_counts": overall_counts,
            "overall_trend": _trend(by_year),
            "directions": directions,
            "total_papers": len(papers_in_range),
            "top_venues": [{"name": v, "count": c} for v, c in venue_counter.most_common(10)],
        }, ensure_ascii=False, default=str)

    # ── Health Check (in-IDE diagnostics) ──────────────────────────────

    @mcp.tool()
    def paper_health() -> str:
        """Run a health check on paper-agent setup. Verifies LLM config, research
        profile, paper library, and workspace. Use this when something seems broken
        or when the user asks to diagnose their setup.

        Returns:
            JSON with per-check pass/fail results and fix suggestions.
        """
        import shutil
        import sys as _sys

        checks: list[dict[str, Any]] = []

        # 1. LLM config
        try:
            from paper_agent.app.config_manager import ConfigManager
            cm = ConfigManager(None)
            if cm.is_initialized():
                checks.append({"name": "llm_config", "pass": True, "detail": "已初始化"})
            else:
                checks.append({"name": "llm_config", "pass": False,
                                "detail": "未初始化",
                                "fix": "在终端运行 paper-agent init"})
        except Exception as e:
            checks.append({"name": "llm_config", "pass": False,
                            "detail": str(e),
                            "fix": "在终端运行 paper-agent init"})

        # 2. MCP executable
        mcp_bin = shutil.which("paper-agent-mcp")
        if mcp_bin:
            checks.append({"name": "mcp_binary", "pass": True, "detail": mcp_bin})
        else:
            venv_bin = Path(_sys.executable).parent / "paper-agent-mcp"
            checks.append({"name": "mcp_binary", "pass": True,
                            "detail": str(venv_bin) if venv_bin.exists()
                            else f"{_sys.executable} -m paper_agent.mcp (fallback)"})

        # 3. Research profile
        try:
            cfg = ctx.require_initialized()
            if cfg.topics:
                checks.append({"name": "profile", "pass": True,
                                "detail": f"{len(cfg.topics)} topics, {len(cfg.keywords)} keywords"})
            else:
                checks.append({"name": "profile", "pass": False,
                                "detail": "未配置研究方向",
                                "fix": "告诉我你的研究方向，或运行 /paper-setup"})
        except Exception:
            checks.append({"name": "profile", "pass": False,
                            "detail": "需要先完成 init",
                            "fix": "在终端运行 paper-agent init"})

        # 4. Paper library
        try:
            total = ctx.storage.count_papers()
            if total > 0:
                checks.append({"name": "library", "pass": True, "detail": f"{total} 篇论文"})
            else:
                checks.append({"name": "library", "pass": False,
                                "detail": "论文库为空",
                                "fix": "运行 /start-my-day 或 /paper-collect 采集论文"})
        except Exception:
            checks.append({"name": "library", "pass": False,
                            "detail": "无法连接论文库",
                            "fix": "检查数据库配置"})

        # 5. Workspace
        try:
            ws_status = ctx.workspace_manager.status()
            checks.append({"name": "workspace", "pass": True,
                            "detail": f"已初始化 — {ws_status.get('total_notes', 0)} 笔记"})
        except Exception:
            checks.append({"name": "workspace", "pass": False,
                            "detail": "工作区未初始化",
                            "fix": "运行 paper-agent setup claude-code 或 paper-agent setup cursor"})

        all_ok = all(c["pass"] for c in checks)
        suggestion = None
        if not all_ok:
            failed = [c for c in checks if not c["pass"]]
            suggestion = "需要修复: " + "; ".join(
                f"{c['name']} — {c.get('fix', c['detail'])}" for c in failed
            )

        return json.dumps({
            "status": "ok" if all_ok else "issues_found",
            "checks": checks,
            "suggestion": suggestion,
        }, ensure_ascii=False, default=str)
