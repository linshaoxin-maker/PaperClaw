"""Application context: lazy-init wiring of storage, config, LLM, services."""

from __future__ import annotations

from collections.abc import Callable
from functools import cached_property
from pathlib import Path

from paper_agent.app.config_manager import ConfigManager, ConfigProfile
from paper_agent.cli.console import console
from paper_agent.domain.exceptions import NotInitializedError
from paper_agent.infra.llm.llm_provider import LLMProvider
from paper_agent.infra.sources.source_registry import SourceRegistry
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage
from paper_agent.services.collection_manager import CollectionManager
from paper_agent.services.credibility_assessor import CredibilityAssessor
from paper_agent.services.digest_generator import DigestGenerator
from paper_agent.services.extraction_engine import ExtractionEngine
from paper_agent.services.feedback_manager import FeedbackManager
from paper_agent.services.filtering_manager import FilteringManager
from paper_agent.services.citation_service import CitationService
from paper_agent.services.pdf_processor import PdfProcessor
from paper_agent.services.research_engine import ResearchEngine
from paper_agent.services.research_planner import ResearchPlanner
from paper_agent.services.search_engine import SearchEngine
from paper_agent.services.source_collector import SourceCollector
from paper_agent.services.watchlist_manager import WatchlistManager
from paper_agent.services.workspace_manager import WorkspaceManager


class AppContext:
    """Singleton-ish holder for all application dependencies."""

    def __init__(
        self,
        config_path: str | Path | None = None,
        debug: bool = False,
        stderr_log: Callable[[str], None] | None = None,
    ) -> None:
        self._config_manager = ConfigManager(config_path)
        self._storage: SQLiteStorage | None = None
        self._debug = debug
        self._stderr_log = stderr_log

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
            provider = OpenAIProvider(api_key=cfg.llm_api_key, model=cfg.llm_model, base_url=cfg.llm_base_url)
        else:
            from paper_agent.infra.llm.anthropic_provider import AnthropicProvider
            provider = AnthropicProvider(api_key=cfg.llm_api_key, model=cfg.llm_model, base_url=cfg.llm_base_url)
        provider.set_storage(self.storage)
        return provider

    @cached_property
    def source_collector(self) -> SourceCollector:
        """SourceCollector with only ArxivAdapter (conferences go through S2)."""
        debug_log = lambda msg: console.print(f"[dim][collect:debug][/dim] {msg}")

        from paper_agent.infra.sources.arxiv_adapter import ArxivAdapter

        collector = SourceCollector(
            debug=self._debug,
            debug_log=debug_log,
        )
        collector.register_adapter(ArxivAdapter(debug=self._debug, debug_log=debug_log))
        return collector

    @cached_property
    def collection_manager(self) -> CollectionManager:
        if self._stderr_log:
            # MCP mode: logs to stderr (stdout reserved for JSON-RPC)
            debug_log = self._stderr_log
            progress_log = self._stderr_log
        else:
            # CLI mode: Rich console output
            debug_log = lambda msg: console.print(f"[dim] {msg}[/dim]")
            progress_log = lambda msg: console.print(f"  {msg}")

        from paper_agent.infra.sources.acl_anthology_adapter import ACLAnthologyAdapter
        from paper_agent.infra.sources.dblp_adapter import DBLPAdapter
        from paper_agent.infra.sources.openalex_adapter import OpenAlexAdapter
        from paper_agent.infra.sources.openreview_adapter import OpenReviewAdapter
        from paper_agent.infra.sources.semantic_scholar_adapter import SemanticScholarAdapter

        adapter_kwargs = {
            "debug": self._debug, "debug_log": debug_log, "progress_log": progress_log,
        }
        return CollectionManager(
            self.storage,
            source_collector=self.source_collector,
            s2_adapter=SemanticScholarAdapter(**adapter_kwargs),
            dblp_adapter=DBLPAdapter(**adapter_kwargs),
            openreview_adapter=OpenReviewAdapter(**adapter_kwargs),
            acl_adapter=ACLAnthologyAdapter(**adapter_kwargs),
            openalex_adapter=OpenAlexAdapter(**adapter_kwargs),
            debug=self._debug,
            debug_log=debug_log,
            progress_log=progress_log,
        )

    @cached_property
    def filtering_manager(self) -> FilteringManager:
        return FilteringManager(
            self.storage, self.llm,
            feedback_manager=self.feedback_manager,
            credibility_assessor=self.credibility_assessor,
        )

    @cached_property
    def search_engine(self) -> SearchEngine:
        profile = None
        try:
            profile = self.config
        except Exception:
            pass
        return SearchEngine(self.storage, profile=profile, feedback_manager=self.feedback_manager)

    @cached_property
    def digest_generator(self) -> DigestGenerator:
        return DigestGenerator(self.storage, feedback_manager=self.feedback_manager)

    @cached_property
    def workspace_manager(self) -> WorkspaceManager:
        cfg = self.config
        workspace_dir = Path(cfg.data_dir)
        return WorkspaceManager(workspace_dir, self.storage)

    @cached_property
    def citation_service(self) -> CitationService:
        return CitationService(self.storage)

    @cached_property
    def pdf_processor(self) -> PdfProcessor:
        return PdfProcessor(self.storage)

    @cached_property
    def extraction_engine(self) -> ExtractionEngine:
        return ExtractionEngine(self.storage, self.llm)

    @cached_property
    def research_engine(self) -> ResearchEngine:
        profile = None
        try:
            profile = self.config
        except Exception:
            pass
        return ResearchEngine(self.search_engine, self.llm, profile=profile)

    @cached_property
    def feedback_manager(self) -> FeedbackManager:
        return FeedbackManager(self.storage)

    @cached_property
    def watchlist_manager(self) -> WatchlistManager:
        return WatchlistManager(self.storage)

    @cached_property
    def credibility_assessor(self) -> CredibilityAssessor:
        return CredibilityAssessor(self.storage, self.llm)

    @cached_property
    def research_planner(self) -> ResearchPlanner:
        context = self.storage.get_research_context() or {}
        return ResearchPlanner(self.storage, self.llm, research_context=context)
