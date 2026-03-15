"""Research planning service: bridge from paper analysis to research action."""

from __future__ import annotations

from typing import Any

from paper_agent.domain.models.paper import Paper
from paper_agent.domain.models.paper_content import PaperContent
from paper_agent.domain.models.paper_profile import PaperProfile
from paper_agent.infra.llm.llm_provider import LLMProvider
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage


class ResearchPlanner:
    def __init__(
        self,
        storage: SQLiteStorage,
        llm: LLMProvider,
        research_context: dict[str, Any] | None = None,
    ) -> None:
        self._storage = storage
        self._llm = llm
        self._context = research_context or {}

    def ideate(self, paper_ids: list[str]) -> dict[str, Any]:
        """Generate research ideas inspired by the given papers."""
        papers_info = self._gather_papers_info(paper_ids)
        if not papers_info:
            return {"error": "No papers found."}

        context_str = self._format_research_context()
        papers_str = self._format_papers(papers_info)

        prompt = (
            f"You are a research advisor. Based on the following papers and research context, "
            f"generate concrete, actionable research ideas.\n\n"
            f"Research Context:\n{context_str}\n\n"
            f"Papers:\n{papers_str}\n\n"
            f"For each idea, provide:\n"
            f"1. 想法名称（一句话）\n"
            f"2. 动机（为什么值得做）\n"
            f"3. 技术路线（概要）\n"
            f"4. 所需资源（数据、算力、时间）\n"
            f"5. 风险评估\n"
            f"6. 相关论文（从上述列表中引用）\n\n"
            f"Generate 3-5 ideas, ranked by feasibility and novelty."
        )

        ideas_text = self._llm.synthesize(prompt)
        return {
            "status": "ok",
            "paper_count": len(papers_info),
            "context": self._context,
            "ideas": ideas_text,
        }

    def experiment_plan(self, paper_id: str) -> dict[str, Any]:
        """Analyze what's reproducible, improvable, and replaceable in a paper."""
        paper = self._storage.get_paper(paper_id)
        if not paper:
            return {"error": f"Paper not found: {paper_id}"}

        profile = self._storage.get_paper_profile(paper_id)
        content = self._storage.get_paper_content(paper_id)

        context_str = self._format_research_context()
        paper_str = f"Title: {paper.title}\nAbstract: {paper.abstract}"
        if profile:
            paper_str += (
                f"\nMethod: {profile.method_name}"
                f"\nDatasets: {', '.join(profile.datasets)}"
                f"\nBaselines: {', '.join(profile.baselines)}"
                f"\nMetrics: {', '.join(profile.metrics)}"
            )
        if content:
            method_section = content.get_section("method")
            if method_section:
                paper_str += f"\n\nMethod Details:\n{method_section.text[:3000]}"
            exp_section = content.get_section("experiments")
            if exp_section:
                paper_str += f"\n\nExperiments:\n{exp_section.text[:3000]}"

        prompt = (
            f"Analyze this paper for research action:\n\n"
            f"Research Context:\n{context_str}\n\n"
            f"Paper:\n{paper_str}\n\n"
            f"Provide:\n"
            f"1. 可复现部分：哪些实验可以直接复现？需要什么？\n"
            f"2. 可改进部分：方法/模型/训练流程哪里有改进空间？\n"
            f"3. 可替换部分：哪些组件可以用我现有的方法替换？\n"
            f"4. 实验计划：具体的实验步骤建议\n"
            f"5. 预期工作量和风险"
        )

        plan_text = self._llm.synthesize(prompt)
        return {
            "status": "ok",
            "paper_id": paper_id,
            "title": paper.title,
            "has_profile": profile is not None,
            "has_fulltext": content is not None,
            "plan": plan_text,
        }

    def reading_pack(self, question: str, limit: int = 10) -> dict[str, Any]:
        """Organize a reading pack for a research question."""
        from paper_agent.services.search_engine import SearchEngine

        search = SearchEngine(self._storage)
        result = search.search(question, limit=limit * 2, diverse=True)
        papers = result.papers[:limit]

        if not papers:
            return {"status": "ok", "message": "未找到相关论文。", "pack": []}

        papers_str = "\n".join(
            f"[{i+1}] {p.title} ({p.published_at.year if p.published_at else 'N/A'}) "
            f"- Score: {p.relevance_score:.1f} - Topics: {', '.join(p.topics[:3])}"
            for i, p in enumerate(papers)
        )

        context_str = self._format_research_context()

        prompt = (
            f"Organize these papers into a reading pack for the question:\n"
            f"'{question}'\n\n"
            f"Research Context:\n{context_str}\n\n"
            f"Papers:\n{papers_str}\n\n"
            f"For each paper, explain:\n"
            f"1. 建议阅读顺序（编号）\n"
            f"2. 阅读理由（一句话）\n"
            f"3. 角色：背景 / 核心方法 / 实验参考 / 最新进展\n"
            f"4. 精读 / 略读 / 选读\n\n"
            f"Return a structured reading plan."
        )

        plan_text = self._llm.synthesize(prompt)
        return {
            "status": "ok",
            "question": question,
            "paper_count": len(papers),
            "papers": [
                {"id": p.id, "title": p.title, "score": round(p.relevance_score, 1)}
                for p in papers
            ],
            "reading_plan": plan_text,
        }

    def _gather_papers_info(self, paper_ids: list[str]) -> list[dict[str, Any]]:
        infos: list[dict[str, Any]] = []
        for pid in paper_ids:
            paper = self._storage.get_paper(pid)
            if not paper:
                continue
            info: dict[str, Any] = {
                "id": paper.id,
                "title": paper.title,
                "abstract": paper.abstract[:500],
                "year": paper.published_at.year if paper.published_at else None,
            }
            profile = self._storage.get_paper_profile(pid)
            if profile:
                info["profile"] = profile.to_comparison_row()
            infos.append(info)
        return infos

    def _format_papers(self, papers_info: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for info in papers_info:
            s = f"- {info['title']} ({info.get('year', 'N/A')})\n  {info['abstract'][:300]}"
            if "profile" in info:
                p = info["profile"]
                s += f"\n  Method: {p.get('method', '')}, Datasets: {p.get('datasets', '')}"
            parts.append(s)
        return "\n".join(parts)

    def _format_research_context(self) -> str:
        if not self._context:
            return "No specific research context set."
        parts: list[str] = []
        if self._context.get("current_project"):
            parts.append(f"Project: {self._context['current_project']}")
        if self._context.get("current_baseline"):
            parts.append(f"Current baseline: {self._context['current_baseline']}")
        if self._context.get("current_questions"):
            parts.append(f"Open questions: {', '.join(self._context['current_questions'])}")
        return "\n".join(parts) if parts else "No specific research context set."
