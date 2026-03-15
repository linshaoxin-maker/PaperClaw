"""Feedback learning service: record user feedback and adjust scoring."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from paper_agent.infra.storage.sqlite_storage import SQLiteStorage


class FeedbackManager:
    def __init__(self, storage: SQLiteStorage) -> None:
        self._storage = storage

    def record_feedback(
        self,
        paper_id: str,
        feedback_type: str,
        value: str,
        context: str = "",
    ) -> dict[str, Any]:
        """Record a piece of user feedback.

        feedback_type:
          - relevance_override: "too_high" | "too_low" | "just_right"
          - topic_preference: "more" | "less" (with topic name in value)
          - skip_reason: free text explaining why skipped
          - highlight: free text explaining why important
        """
        valid_types = {"relevance_override", "topic_preference", "skip_reason", "highlight"}
        if feedback_type not in valid_types:
            return {"error": f"Invalid feedback_type. Use: {sorted(valid_types)}"}

        self._storage.save_feedback(paper_id, feedback_type, value, context)
        return {"status": "ok", "paper_id": paper_id, "type": feedback_type, "value": value}

    def compute_preference_adjustments(self) -> dict[str, Any]:
        """Aggregate all feedback into scoring adjustments.

        Returns topic weight boosts/penalties and keyword adjustments.
        """
        all_feedback = self._storage.get_all_feedback()

        topic_adjustments: dict[str, float] = defaultdict(float)
        relevance_bias: float = 0.0
        relevance_count: int = 0

        for fb in all_feedback:
            if fb["feedback_type"] == "topic_preference":
                topic = fb["value"].split(":", 1)[-1].strip() if ":" in fb["value"] else fb["value"]
                direction = fb["value"].split(":", 1)[0].strip() if ":" in fb["value"] else "more"
                if direction == "more":
                    topic_adjustments[topic] += 0.1
                elif direction == "less":
                    topic_adjustments[topic] -= 0.1

            elif fb["feedback_type"] == "relevance_override":
                if fb["value"] == "too_high":
                    relevance_bias -= 0.5
                elif fb["value"] == "too_low":
                    relevance_bias += 0.5
                relevance_count += 1

        skip_reasons = Counter[str]()
        highlight_topics: list[str] = []
        for fb in all_feedback:
            if fb["feedback_type"] == "skip_reason":
                skip_reasons[fb["value"]] += 1
            elif fb["feedback_type"] == "highlight":
                paper = self._storage.get_paper(fb["paper_id"])
                if paper:
                    highlight_topics.extend(paper.topics)

        avg_bias = relevance_bias / max(relevance_count, 1)

        return {
            "topic_adjustments": dict(topic_adjustments),
            "relevance_bias": round(avg_bias, 2),
            "total_feedback": len(all_feedback),
            "common_skip_reasons": skip_reasons.most_common(5),
            "highlighted_topics": Counter(highlight_topics).most_common(10),
        }

    def get_adjusted_topic_weights(self) -> dict[str, float]:
        """Return topic-level weight adjustments for the reranking formula."""
        adjustments = self.compute_preference_adjustments()
        return adjustments.get("topic_adjustments", {})

    def get_feedback_summary(self) -> dict[str, Any]:
        """Summary of all recorded feedback."""
        all_feedback = self._storage.get_all_feedback()
        by_type = Counter(fb["feedback_type"] for fb in all_feedback)
        return {
            "total": len(all_feedback),
            "by_type": dict(by_type),
            "adjustments": self.compute_preference_adjustments(),
        }
