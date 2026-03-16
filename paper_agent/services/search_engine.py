"""Search engine: FTS5-based retrieval with profile-aware reranking.

Features:
  - Keyword expansion: synonym mapping + profile keyword augmentation
  - Diverse search: auto-expand query and merge results from multiple variants
  - Smart suggestions: when results are few, suggest online/diverse search
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from paper_agent.app.config_manager import ConfigProfile
from paper_agent.domain.models.paper import Paper
from paper_agent.domain.models.query_result import QueryResult
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage

# ── Synonym / abbreviation map (bidirectional) ──

_SYNONYM_GROUPS: list[list[str]] = [
    # ── Deep learning fundamentals ──
    ["GNN", "graph neural network"],
    ["CNN", "convolutional neural network"],
    ["RNN", "recurrent neural network"],
    ["LSTM", "long short-term memory"],
    ["GAN", "generative adversarial network"],
    ["VAE", "variational autoencoder"],
    ["RL", "reinforcement learning"],
    ["NLP", "natural language processing"],
    ["LLM", "large language model"],
    ["transformer", "attention mechanism"],
    ["diffusion model", "denoising diffusion"],
    ["BERT", "bidirectional encoder representations"],
    ["GPT", "generative pre-trained transformer"],
    ["GCN", "graph convolutional network"],
    ["MLP", "multilayer perceptron"],
    ["KG", "knowledge graph"],
    ["RAG", "retrieval augmented generation"],
    ["ViT", "vision transformer"],
    ["DNN", "deep neural network"],
    ["federated learning", "FL"],
    ["contrastive learning", "SimCLR", "MoCo"],
    ["graph transformer", "graph attention"],
    ["zero-shot", "zero shot learning"],
    ["few-shot", "few shot learning"],
    ["meta-learning", "learning to learn"],
    # ── EDA / chip design ──
    ["EDA", "electronic design automation"],
    ["VLSI", "very large scale integration"],
    ["HLS", "high-level synthesis"],
    ["PnR", "place and route", "placement and routing"],
    ["STA", "static timing analysis"],
    ["DRC", "design rule checking"],
    ["netlist", "circuit netlist"],
    ["floorplan", "floorplanning"],
    ["FPGA", "field programmable gate array"],
    ["ASIC", "application specific integrated circuit"],
    # ── LLM agents & tool use ──
    ["LLM agent", "language model agent", "AI agent"],
    ["tool use", "tool calling", "function calling", "tool-augmented LLM"],
    ["MCP", "Model Context Protocol", "model context protocol"],
    ["agentic AI", "autonomous agent", "AI agent system"],
    ["multi-agent", "multi agent system", "agent collaboration"],
    ["agent framework", "agent orchestration"],
    ["ReAct", "reasoning and acting", "chain-of-thought agent"],
    ["code agent", "coding agent", "software agent"],
    ["web agent", "browser agent", "GUI agent"],
    # ── Agent memory & learning ──
    ["agent memory", "memory-augmented agent", "memory module"],
    ["episodic memory", "episodic recall", "event memory"],
    ["procedural memory", "skill memory", "action memory"],
    ["working memory", "context window management"],
    ["long-term memory", "persistent memory", "external memory"],
    ["memory retrieval", "memory consolidation"],
    ["lifelong learning", "continual learning", "never-ending learning"],
    ["self-evolving agent", "self-improving agent", "adaptive agent"],
    ["experience replay", "experience-driven learning"],
    ["skill acquisition", "skill learning", "skill evolution"],
    ["in-context learning", "ICL", "few-shot prompting"],
    # ── Agent evaluation & safety ──
    ["agent benchmark", "AgentBench", "agent evaluation"],
    ["prompt injection", "jailbreak", "adversarial prompt"],
    ["tool poisoning", "malicious tool", "tool security"],
    ["agent safety", "AI safety", "alignment"],
    ["hallucination", "factual grounding", "faithfulness"],
    # ── RAG & retrieval ──
    ["retrieval augmented generation", "RAG", "grounded generation"],
    ["dense retrieval", "neural retrieval", "semantic search"],
    ["knowledge base", "external knowledge", "knowledge retrieval"],
]

_SYNONYM_MAP: dict[str, list[str]] = {}

def _build_synonym_map() -> None:
    for group in _SYNONYM_GROUPS:
        lower_group = [t.lower() for t in group]
        for term in lower_group:
            others = [t for t in lower_group if t != term]
            if term in _SYNONYM_MAP:
                existing = set(_SYNONYM_MAP[term])
                existing.update(others)
                _SYNONYM_MAP[term] = list(existing)
            else:
                _SYNONYM_MAP[term] = others

_build_synonym_map()


@dataclass
class SearchSuggestion:
    """A suggested follow-up action when search results are limited."""
    type: str          # "online_search" | "diverse_search" | "expand_keywords"
    message: str
    expanded_query: str | None = None
    expanded_terms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d: dict = {"type": self.type, "message": self.message}
        if self.expanded_query:
            d["expanded_query"] = self.expanded_query
        if self.expanded_terms:
            d["expanded_terms"] = self.expanded_terms
        return d


class SearchEngine:
    def __init__(
        self,
        storage: SQLiteStorage,
        profile: ConfigProfile | None = None,
        feedback_manager: Any | None = None,
    ) -> None:
        self._storage = storage
        self._profile = profile
        self._feedback_manager = feedback_manager

    def update_profile(self, profile: ConfigProfile) -> None:
        self._profile = profile

    # ── Main search ──

    def search(
        self,
        query: str,
        limit: int = 50,
        mode: str = "retrieval",
        diverse: bool = False,
    ) -> QueryResult:
        """Search local library with optional keyword expansion.

        Args:
            diverse: If True, auto-expand keywords via synonyms + profile,
                     run multiple queries and merge/deduplicate results.
        """
        if diverse:
            papers = self._diverse_search(query, limit)
        else:
            fetch_limit = limit * 3 if self._profile else limit
            papers = self._storage.search_papers(query, limit=fetch_limit)

        if self._profile and papers:
            papers = self._rerank(papers)

        suggestions = self._generate_suggestions(query, papers, limit, diverse)

        result = QueryResult(
            query=query,
            mode=mode,
            papers=papers[:limit],
            status="completed" if papers else "empty",
        )
        result.suggestions = suggestions
        return result

    # ── Diverse search: expand + merge ──

    def _diverse_search(self, query: str, limit: int) -> list[Paper]:
        """Run the original query + expanded variants, merge and deduplicate."""
        variants = self._expand_query(query)
        all_queries = [query] + [v for v in variants if v.lower() != query.lower()]

        seen_ids: set[str] = set()
        merged: list[Paper] = []
        fetch_per = max(limit * 2 // max(len(all_queries), 1), 10)

        for q in all_queries:
            try:
                papers = self._storage.search_papers(q, limit=fetch_per)
            except Exception:
                continue
            for p in papers:
                key = p.canonical_key or p.id
                if key not in seen_ids:
                    seen_ids.add(key)
                    merged.append(p)

        return merged

    # ── Keyword expansion ──

    def _expand_query(self, query: str) -> list[str]:
        """Generate expanded query variants from synonyms + profile keywords."""
        expansions: list[str] = []
        query_lower = query.lower()
        words = query_lower.split()

        # 1) Synonym expansion: replace each known term with its synonyms
        for term, synonyms in _SYNONYM_MAP.items():
            if term in query_lower:
                for syn in synonyms[:2]:
                    expanded = query_lower.replace(term, syn)
                    if expanded != query_lower:
                        expansions.append(expanded)

        # 2) Profile augmentation: add profile keywords related to the query
        if self._profile:
            profile_terms = (self._profile.topics or []) + (self._profile.keywords or [])
            related = [
                t for t in profile_terms
                if t.lower() not in query_lower
                and any(w in t.lower() or t.lower() in w for w in words)
            ]
            if related:
                augmented = query + " " + " ".join(related[:3])
                expansions.append(augmented)

        return expansions[:5]

    def get_expansions(self, query: str) -> list[str]:
        """Public API: get possible keyword expansions for a query."""
        return self._expand_query(query)

    # ── Suggestions ──

    def _generate_suggestions(
        self,
        query: str,
        papers: list[Paper],
        limit: int,
        already_diverse: bool,
    ) -> list[SearchSuggestion]:
        """Generate smart suggestions when results are limited."""
        suggestions: list[SearchSuggestion] = []
        count = len(papers)

        # Threshold: suggest if results < 50% of requested limit
        needs_more = count < max(limit // 2, 3)

        if needs_more and not already_diverse:
            expansions = self._expand_query(query)
            if expansions:
                suggestions.append(SearchSuggestion(
                    type="diverse_search",
                    message=(
                        f"本地只找到 {count} 篇结果。"
                        f"可以尝试多样性搜索，自动扩展关键词: "
                        f"{', '.join(expansions[:3])}"
                    ),
                    expanded_query=expansions[0] if expansions else None,
                    expanded_terms=expansions[:3],
                ))

        if needs_more:
            suggestions.append(SearchSuggestion(
                type="online_search",
                message=(
                    f"本地结果较少({count} 篇)。"
                    "可以尝试在线搜索 (paper_search_online) 从 arXiv 实时获取更多结果。"
                ),
            ))

        if count == 0:
            suggestions.append(SearchSuggestion(
                type="collect_first",
                message="本地库为空或未命中。建议先执行 paper-agent collect 采集论文，再搜索。",
            ))

        return suggestions

    # ── Profile-aware reranking ──

    def rank_results(self, papers: list[Paper], query: str) -> list[Paper]:
        if self._profile:
            return self._rerank(papers)
        return sorted(papers, key=lambda p: p.relevance_score, reverse=True)

    def _rerank(self, papers: list[Paper]) -> list[Paper]:
        """Re-score papers using profile topics/keywords + recency + LLM score + feedback."""
        assert self._profile is not None
        profile_topics = {t.lower() for t in self._profile.topics}
        profile_keywords = {k.lower() for k in self._profile.keywords}

        # Get feedback adjustments if available
        feedback_weights: dict[str, float] = {}
        if self._feedback_manager:
            try:
                feedback_weights = self._feedback_manager.get_adjusted_topic_weights()
            except Exception:
                pass

        scored: list[tuple[float, Paper]] = []
        for i, p in enumerate(papers):
            fts_score = 1.0 - (i / max(len(papers), 1))

            paper_topics = {t.lower() for t in p.topics}
            topic_overlap = len(paper_topics & profile_topics)
            topic_score = min(topic_overlap / max(len(profile_topics), 1), 1.0)

            text = (p.title + " " + p.abstract).lower()
            kw_hits = sum(1 for kw in profile_keywords if kw in text)
            kw_score = min(kw_hits / max(len(profile_keywords), 1), 1.0)

            recency_score = _recency_score(p.published_at)

            llm_score = min(p.relevance_score / 10.0, 1.0) if p.relevance_score else 0.0

            # Apply feedback offset (normalized to 0-1 range)
            feedback_offset = 0.0
            if feedback_weights:
                for topic in p.topics:
                    if topic.lower() in feedback_weights:
                        feedback_offset += feedback_weights[topic.lower()]
                feedback_offset = max(-0.2, min(0.2, feedback_offset))

            final = (
                0.30 * fts_score
                + 0.20 * topic_score
                + 0.20 * kw_score
                + 0.15 * llm_score
                + 0.10 * recency_score
                + 0.05 + feedback_offset  # base + feedback adjustment
            )
            scored.append((final, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored]


def _recency_score(published_at: datetime | None) -> float:
    """Exponential decay: 1.0 for today, ~0.5 at 30 days, ~0 at 90+ days."""
    if not published_at:
        return 0.0
    now = datetime.now(timezone.utc)
    pub = published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc)
    days_old = max((now - pub).days, 0)
    return math.exp(-0.023 * days_old)
