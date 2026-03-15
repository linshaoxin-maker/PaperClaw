"""LLM provider abstraction for relevance scoring, topic classification, and synthesis."""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from typing import Any

from paper_agent.domain.models.paper import Paper


class LLMProvider(ABC):
    _storage: Any = None  # Set by AppContext for cache support

    def set_storage(self, storage: Any) -> None:
        """Inject storage for LLM response caching."""
        self._storage = storage

    @abstractmethod
    def score_relevance(
        self, paper: Paper, interests: dict[str, Any]
    ) -> dict[str, Any]:
        """Return {"score": float, "band": str, "reason": str, "topics": list[str]}."""

    @abstractmethod
    def classify_topics(self, paper: Paper) -> list[str]:
        ...

    @abstractmethod
    def extract_methodology(self, text: str) -> list[str]:
        ...

    @abstractmethod
    def extract_objectives(self, text: str) -> list[str]:
        ...

    @abstractmethod
    def synthesize(self, prompt: str) -> str:
        ...

    def _cache_key(self, task_type: str, input_data: str) -> str:
        """Generate a deterministic cache key."""
        h = hashlib.sha256(input_data.encode()).hexdigest()[:16]
        return f"{task_type}:{h}"

    def _get_cached(self, task_type: str, input_data: str) -> str | None:
        """Try to get a cached LLM response."""
        if not self._storage:
            return None
        try:
            key = self._cache_key(task_type, input_data)
            return self._storage.get_llm_cache(key)
        except Exception:
            return None

    def _set_cached(self, task_type: str, input_data: str, response: str) -> None:
        """Cache an LLM response."""
        if not self._storage:
            return
        try:
            key = self._cache_key(task_type, input_data)
            h = hashlib.sha256(input_data.encode()).hexdigest()[:16]
            self._storage.set_llm_cache(
                cache_key=key,
                provider=self.__class__.__name__,
                model="",
                task_type=task_type,
                input_hash=h,
                response_json=response,
            )
        except Exception:
            pass

    # ── v04-experience: Batch scoring ──

    def score_relevance_batch(
        self, papers: list[Paper], interests: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Score multiple papers in a single LLM call.

        Returns a list of dicts with the same keys as score_relevance().
        Length of returned list equals len(papers).
        On parse failure, returns default low scores for all papers.
        Uses LLM cache when available.
        """
        # Check cache for each paper individually
        topics_str = ", ".join(interests.get("topics", []))
        keywords_str = ", ".join(interests.get("keywords", []))
        cache_input = json.dumps([p.canonical_key or p.id for p in papers]) + topics_str + keywords_str
        cached = self._get_cached("batch_score", cache_input)
        if cached:
            try:
                results = json.loads(cached)
                if isinstance(results, list) and len(results) == len(papers):
                    return results
            except (json.JSONDecodeError, TypeError):
                pass

        paper_blocks = []
        for i, p in enumerate(papers, 1):
            abstract_short = p.abstract[:400] if p.abstract else "(no abstract)"
            paper_blocks.append(
                f"Paper {i}:\n- Title: {p.title}\n- Abstract: {abstract_short}"
            )

        prompt = (
            f"Evaluate each paper's relevance to the research interests below.\n\n"
            f"Research interests:\n"
            f"- Topics: {topics_str}\n"
            f"- Keywords: {keywords_str}\n\n"
            + "\n\n".join(paper_blocks)
            + "\n\nReturn a JSON array with one object per paper, in order. "
            f"Each object must have:\n"
            f'- "score": float 0.0-10.0\n'
            f'- "band": "high" if score >= 7.0, else "low"\n'
            f'- "reason": brief explanation in Chinese (1-2 sentences)\n'
            f'- "topics": list of topic tags\n\n'
            f"Return ONLY the JSON array, no markdown."
        )

        raw = self.synthesize(prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]

        try:
            results = json.loads(raw)
            if not isinstance(results, list) or len(results) != len(papers):
                raise ValueError("batch result length mismatch")
            out = []
            for r in results:
                score = float(r.get("score", 0))
                out.append({
                    "score": score,
                    "band": "high" if score >= 7.0 else "low",
                    "reason": r.get("reason", ""),
                    "topics": r.get("topics", []),
                })
            self._set_cached("batch_score", cache_input, json.dumps(out))
            return out
        except (json.JSONDecodeError, ValueError, TypeError):
            return [
                {"score": 0.0, "band": "low", "reason": "batch解析失败", "topics": []}
                for _ in papers
            ]

    # ── v04: Deep understanding methods ──

    def extract_structured(self, text: str, schema: dict[str, str]) -> dict[str, Any]:
        """Extract structured fields from text according to a schema.

        schema: dict mapping field_name -> description of what to extract.
        Returns a dict with the same keys populated from the text.
        """
        schema_desc = "\n".join(f'- "{k}": {v}' for k, v in schema.items())
        prompt = (
            f"Extract the following structured information from this academic paper text.\n\n"
            f"Text:\n{text[:15000]}\n\n"
            f"Fields to extract:\n{schema_desc}\n\n"
            f"Return a JSON object with these exact keys. "
            f"Use null for fields not found. Lists should be JSON arrays. "
            f"Return ONLY the JSON object, no markdown."
        )
        raw = self.synthesize(prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def answer_from_content(self, sections_text: str, question: str) -> str:
        """Answer a question using paper section text as context."""
        prompt = (
            f"Based on the following paper content, answer the question.\n\n"
            f"Paper content:\n{sections_text[:20000]}\n\n"
            f"Question: {question}\n\n"
            f"Answer in Chinese. Be specific and cite relevant details from the text."
        )
        return self.synthesize(prompt)

    def decompose_question(
        self, question: str, profile: Any | None = None
    ) -> dict[str, Any]:
        """Decompose a research question into a search plan."""
        profile_str = ""
        if profile:
            topics = getattr(profile, "topics", [])
            keywords = getattr(profile, "keywords", [])
            if topics or keywords:
                profile_str = (
                    f"\nResearcher's profile:\n"
                    f"- Topics: {', '.join(topics)}\n"
                    f"- Keywords: {', '.join(keywords)}\n"
                )

        prompt = (
            f"A researcher asks: \"{question}\"\n"
            f"{profile_str}\n"
            f"Decompose this into a search plan. Return a JSON object with:\n"
            f'- "search_queries": list of 2-5 search queries to find relevant papers\n'
            f'- "judgment_dimensions": list of criteria to evaluate results\n'
            f'- "exclusion_criteria": list of what to filter out\n'
            f'- "evidence_needed": list of evidence types needed to answer\n\n'
            f"Return ONLY the JSON object, no markdown."
        )
        raw = self.synthesize(prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"search_queries": [question]}

    def explain_relevance(
        self,
        paper: Paper,
        research_context: dict[str, Any],
        reading_list_titles: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate a research-context-aware recommendation explanation."""
        context_parts: list[str] = []
        if research_context.get("current_project"):
            context_parts.append(f"Project: {research_context['current_project']}")
        if research_context.get("current_baseline"):
            context_parts.append(f"Baseline: {research_context['current_baseline']}")
        if research_context.get("current_questions"):
            context_parts.append(f"Questions: {', '.join(research_context['current_questions'])}")

        reading_str = ""
        if reading_list_titles:
            reading_str = f"\nCurrent reading list:\n" + "\n".join(f"- {t}" for t in reading_list_titles[:20])

        prompt = (
            f"Evaluate this paper's relevance to the researcher's current work.\n\n"
            f"Research context:\n{chr(10).join(context_parts)}\n"
            f"{reading_str}\n\n"
            f"Paper:\n- Title: {paper.title}\n- Abstract: {paper.abstract[:500]}\n\n"
            f"Return a JSON object with:\n"
            f'- "relevance_to_project": how it relates to the current project (Chinese, 1-2 sentences)\n'
            f'- "gap_filled": one of "background", "method", "experiment", "latest"\n'
            f'- "similar_in_list": list of titles from reading list that are most similar\n'
            f'- "priority_reason": why read this before others (Chinese, 1 sentence)\n\n'
            f"Return ONLY the JSON object, no markdown."
        )
        raw = self.synthesize(prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "relevance_to_project": paper.recommendation_reason,
                "gap_filled": "unknown",
                "similar_in_list": [],
                "priority_reason": "",
            }

    # ── v05: Credibility assessment ──

    def assess_credibility(self, text: str) -> dict[str, Any]:
        """Assess the credibility of a paper based on its text."""
        prompt = (
            f"Assess the credibility and reproducibility of this paper.\n\n"
            f"Paper:\n{text[:10000]}\n\n"
            f"Return a JSON object with:\n"
            f'- "open_data": boolean, whether the paper mentions using/releasing open datasets\n'
            f'- "claim_aggressiveness": "conservative" | "moderate" | "aggressive"\n'
            f'- "baseline_completeness": "comprehensive" | "adequate" | "insufficient"\n'
            f'- "reproducibility_risk": "low" | "medium" | "high"\n'
            f'- "overall_confidence": "high" | "medium" | "low"\n'
            f'- "notes": brief assessment notes in Chinese (2-3 sentences)\n\n'
            f"Return ONLY the JSON object, no markdown."
        )
        raw = self.synthesize(prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "open_data": None,
                "claim_aggressiveness": "unknown",
                "baseline_completeness": "unknown",
                "reproducibility_risk": "unknown",
                "overall_confidence": "unknown",
                "notes": "LLM 解析失败",
            }
