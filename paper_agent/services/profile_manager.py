"""Profile manager.

Creates/updates a user's research profile (topics/keywords) and integrates with
SourceRegistry to recommend and enable sources.

MVP: primarily template + manual flows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paper_agent.app.config_manager import ConfigManager, ConfigProfile
from paper_agent.infra.sources.source_registry import SourceRegistry


@dataclass(frozen=True)
class ProfileResult:
    topics: list[str]
    keywords: list[str]
    enabled_source_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "topics": self.topics,
            "keywords": self.keywords,
            "enabled_sources": self.enabled_source_ids,
        }


class ProfileManager:
    def __init__(self, config_manager: ConfigManager, source_registry: SourceRegistry) -> None:
        self._config_manager = config_manager
        self._source_registry = source_registry

    def apply_profile(
        self,
        *,
        topics: list[str],
        keywords: list[str],
        enable_sources: list[str],
    ) -> ProfileResult:
        cfg = self._config_manager.load_config()

        cfg.topics = topics
        cfg.keywords = keywords

        # Keep cfg.sources for backward compatibility (arXiv categories only).
        # We sync it from enabled arXiv category sources.
        self._source_registry.enable(enable_sources)
        enabled = self._source_registry.list_enabled_sources()
        arxiv_cats = [s.api_config.get("category") for s in enabled if s.api_type == "arxiv" and s.api_config]
        cfg.sources = [c for c in arxiv_cats if isinstance(c, str) and c]

        cfg.profile_completed = True

        self._config_manager.save_config(cfg)

        return ProfileResult(
            topics=cfg.topics,
            keywords=cfg.keywords,
            enabled_source_ids=[s.id for s in enabled],
        )
