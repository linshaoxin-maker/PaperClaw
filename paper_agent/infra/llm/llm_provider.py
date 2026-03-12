"""LLM provider abstraction for relevance scoring, topic classification, and synthesis."""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from typing import Any

from paper_agent.domain.models.paper import Paper


class LLMProvider(ABC):
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
