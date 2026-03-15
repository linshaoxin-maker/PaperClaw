"""Research question engine: problem-driven search with question decomposition."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from paper_agent.app.config_manager import ConfigProfile
from paper_agent.domain.models.paper import Paper
from paper_agent.infra.llm.llm_provider import LLMProvider
from paper_agent.services.search_engine import SearchEngine


@dataclass
class QuestionPlan:
    original_question: str
    search_queries: list[str] = field(default_factory=list)
    judgment_dimensions: list[str] = field(default_factory=list)
    exclusion_criteria: list[str] = field(default_factory=list)
    evidence_needed: list[str] = field(default_factory=list)


class ResearchEngine:
    def __init__(
        self,
        search_engine: SearchEngine,
        llm: LLMProvider,
        profile: ConfigProfile | None = None,
    ) -> None:
        self._search = search_engine
        self._llm = llm
        self._profile = profile

    def research(
        self,
        question: str,
        limit: int = 20,
        supplement_online: bool = True,
    ) -> dict[str, Any]:
        """Decompose a research question, execute multi-query search, and synthesize an answer."""
        plan = self._decompose(question)

        all_papers: list[Paper] = []
        seen: set[str] = set()
        query_results: list[dict[str, Any]] = []

        for query in plan.search_queries:
            result = self._search.search(query, limit=limit, diverse=True)
            papers_found: list[Paper] = []
            for p in result.papers:
                key = p.canonical_key or p.id
                if key not in seen:
                    seen.add(key)
                    all_papers.append(p)
                    papers_found.append(p)
            query_results.append({
                "query": query,
                "found": len(papers_found),
            })

        if supplement_online and len(all_papers) < limit:
            for query in plan.search_queries[:2]:
                try:
                    from concurrent.futures import ThreadPoolExecutor, as_completed

                    from paper_agent.infra.sources.arxiv_adapter import (
                        ARXIV_API_URL,
                        ArxivAdapter,
                    )

                    def _search_online(q: str) -> list[Paper]:
                        import httpx
                        adapter = ArxivAdapter()
                        search_q = "+AND+".join(f"all:{w}" for w in q.split() if w.strip())
                        url = (
                            f"{ARXIV_API_URL}?search_query={search_q}"
                            f"&start=0&max_results={limit}&sortBy=relevance"
                        )
                        client = httpx.Client(timeout=30.0, follow_redirects=True, trust_env=True)
                        try:
                            resp = client.get(url)
                            return adapter._parse_response(resp.text) if resp.status_code == 200 else []
                        finally:
                            client.close()

                    online = _search_online(query)
                    for p in online:
                        key = p.canonical_key or p.id
                        if key not in seen:
                            seen.add(key)
                            all_papers.append(p)
                except Exception:
                    pass

        if self._search._profile:
            all_papers = self._search.rank_results(all_papers, question)
        else:
            all_papers.sort(key=lambda p: p.relevance_score or 0, reverse=True)

        top_papers = all_papers[:limit]

        answer = self._synthesize_answer(plan, top_papers)

        return {
            "status": "ok",
            "question": question,
            "plan": {
                "search_queries": plan.search_queries,
                "judgment_dimensions": plan.judgment_dimensions,
                "exclusion_criteria": plan.exclusion_criteria,
                "evidence_needed": plan.evidence_needed,
            },
            "query_results": query_results,
            "total_candidates": len(all_papers),
            "papers": [
                {
                    "id": p.id,
                    "title": p.title,
                    "authors": p.authors[:3] if p.authors else [],
                    "year": p.published_at.year if p.published_at else None,
                    "score": round(p.relevance_score, 1) if p.relevance_score else None,
                    "abstract_snippet": (p.abstract or "")[:200],
                }
                for p in top_papers
            ],
            "answer": answer,
        }

    def _decompose(self, question: str) -> QuestionPlan:
        """Use LLM to decompose a research question into a search plan."""
        raw = self._llm.decompose_question(question, self._profile)
        return QuestionPlan(
            original_question=question,
            search_queries=raw.get("search_queries", [question]),
            judgment_dimensions=raw.get("judgment_dimensions", []),
            exclusion_criteria=raw.get("exclusion_criteria", []),
            evidence_needed=raw.get("evidence_needed", []),
        )

    def _synthesize_answer(self, plan: QuestionPlan, papers: list[Paper]) -> str:
        """Synthesize an evidence-based answer from the papers found."""
        if not papers:
            return "未找到相关论文，无法回答该研究问题。"

        papers_context = "\n".join(
            f"- [{p.title}] ({p.published_at.year if p.published_at else 'N/A'}): "
            f"{(p.abstract or '')[:200]}"
            for p in papers[:10]
        )

        prompt = (
            f"Based on the following papers, answer this research question:\n\n"
            f"Question: {plan.original_question}\n\n"
            f"Judgment dimensions: {', '.join(plan.judgment_dimensions)}\n\n"
            f"Papers found:\n{papers_context}\n\n"
            f"Provide a structured answer in Chinese with:\n"
            f"1. 直接回答\n"
            f"2. 支撑证据（引用具体论文）\n"
            f"3. 不确定性和信息缺口\n"
            f"4. 建议的后续研究方向"
        )

        return self._llm.synthesize(prompt)
