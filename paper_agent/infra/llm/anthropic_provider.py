"""Anthropic Claude LLM provider implementation."""

from __future__ import annotations

import json
from typing import Any

import anthropic

from paper_agent.domain.models.paper import Paper
from paper_agent.infra.llm.llm_provider import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "", base_url: str = "") -> None:
        self._client = anthropic.Anthropic(
            api_key=api_key,
            base_url=base_url if base_url else None,
            timeout=60.0,
            max_retries=2,
        )
        self._model = model or "claude-sonnet-4-20250514"

    def score_relevance(
        self, paper: Paper, interests: dict[str, Any]
    ) -> dict[str, Any]:
        topics_str = ", ".join(interests.get("topics", []))
        keywords_str = ", ".join(interests.get("keywords", []))

        prompt = f"""Evaluate this paper's relevance to the research interests below.

Research interests:
- Topics: {topics_str}
- Keywords: {keywords_str}

Paper:
- Title: {paper.title}
- Abstract: {paper.abstract}

Return a JSON object with:
- "score": a float from 0.0 to 10.0
- "band": "high" if score >= 7.0, else "low"
- "reason": a brief explanation in Chinese (1-2 sentences)
- "topics": a list of topic tags for this paper

Return ONLY the JSON object, no markdown."""

        raw = self._call(prompt)
        try:
            result = json.loads(raw)
            score = float(result.get("score", 0))
            return {
                "score": score,
                "band": "high" if score >= 7.0 else "low",
                "reason": result.get("reason", ""),
                "topics": result.get("topics", []),
            }
        except (json.JSONDecodeError, ValueError):
            return {"score": 0.0, "band": "low", "reason": "解析失败", "topics": []}

    def classify_topics(self, paper: Paper) -> list[str]:
        prompt = f"""Classify this paper into research topics/tags.

Title: {paper.title}
Abstract: {paper.abstract}

Return a JSON array of topic strings. Return ONLY the JSON array."""

        raw = self._call(prompt)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    def extract_methodology(self, text: str) -> list[str]:
        prompt = f"""Extract the key methods, techniques, algorithms, and frameworks mentioned in this text.

Text: {text}

Return a JSON array of method/technique tag strings. Return ONLY the JSON array."""

        raw = self._call(prompt)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    def extract_objectives(self, text: str) -> list[str]:
        prompt = f"""Extract the research objectives and problems this text is trying to solve.

Text: {text}

Return a JSON array of objective/problem description strings. Return ONLY the JSON array."""

        raw = self._call(prompt)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    def synthesize(self, prompt: str) -> str:
        return self._call(prompt)

    def _call(self, prompt: str) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
