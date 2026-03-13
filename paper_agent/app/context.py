"""Application context: lazy-init wiring of storage, config, LLM, services."""

from __future__ import annotations

from functools import cached_property
from pathlib import Path

from paper_agent.app.config_manager import ConfigManager, ConfigProfile
from paper_agent.cli.console import console
from paper_agent.domain.exceptions import NotInitializedError
from paper_agent.infra.llm.llm_provider import LLMProvider
from paper_agent.infra.sources.source_registry import SourceRegistry
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage
from paper_agent.services.collection_manager import CollectionManager
from paper_agent.services.digest_generator import DigestGenerator
from paper_agent.services.filtering_manager import FilteringManager
from paper_agent.services.search_engine import SearchEngine


class AppContext:
    """Singleton-ish holder for all application dependencies."""

    def __init__(self, config_path: str | Path | None = None, debug: bool = False) -> None:
        self._config_manager = ConfigManager(config_path)
        self._storage: SQLiteStorage | None = None
        self._debug = debug

    @property
    def config_manager(self) -> ConfigManager:
        return self._config_manager

    def require_initialized(self) -> ConfigProfile:
        if not self._config_manager.is_initialized():
            raise NotInitializedError()
        return self._config_manager.load_config()

    @cached_property
    def config(self) -> ConfigProfile:
        return self.require_initialized()

    @cached_property
    def storage(self) -> SQLiteStorage:
        cfg = self.config
        storage = SQLiteStorage(cfg.db_path)
        storage.initialize()
        return storage

    @cached_property
    def source_registry(self) -> SourceRegistry:
        cfg = self.config
        user_sources_path = Path(cfg.data_dir) / "sources.yaml"
        return SourceRegistry(user_sources_path=user_sources_path)

    @cached_property
    def llm(self) -> LLMProvider:
        cfg = self.config
        if cfg.llm_provider == "openai":
            from paper_agent.infra.llm.openai_provider import OpenAIProvider
            return OpenAIProvider(api_key=cfg.llm_api_key, model=cfg.llm_model, base_url=cfg.llm_base_url)
        else:
            from paper_agent.infra.llm.anthropic_provider import AnthropicProvider
            return AnthropicProvider(api_key=cfg.llm_api_key, model=cfg.llm_model, base_url=cfg.llm_base_url)

    @cached_property
    def collection_manager(self) -> CollectionManager:
        return CollectionManager(
            self.storage,
            debug=self._debug,
            debug_log=lambda message: console.print(f"[dim][collect:debug][/dim] {message}"),
        )

    @cached_property
    def filtering_manager(self) -> FilteringManager:
        return FilteringManager(self.storage, self.llm)

    @cached_property
    def search_engine(self) -> SearchEngine:
        return SearchEngine(self.storage)

    @cached_property
    def digest_generator(self) -> DigestGenerator:
        return DigestGenerator(self.storage)
