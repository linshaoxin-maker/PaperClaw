"""Abstract base class for all paper source adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime

from paper_agent.domain.models.paper import Paper


class SourceAdapter(ABC):
    """Unified interface for fetching papers from any source (arXiv, DBLP, etc.)."""

    def __init__(
        self,
        debug: bool = False,
        debug_log: Callable[[str], None] | None = None,
        progress_log: Callable[[str], None] | None = None,
    ) -> None:
        self._debug = debug
        self._debug_log = debug_log
        self._progress_log = progress_log

    @property
    @abstractmethod
    def api_type(self) -> str:
        """Identifier matching SourceDefinition.api_type (e.g. 'arxiv', 'dblp')."""

    @property
    def rate_limit_delay(self) -> float:
        """Seconds to sleep between requests to this API."""
        return 1.0

    @abstractmethod
    def collect(
        self,
        api_config: dict,
        since: datetime | None = None,
        max_results: int = 200,
    ) -> list[Paper]:
        """Fetch papers from a single source entry (one category / venue).

        Args:
            api_config: Source-specific config from SourceDefinition.api_config.
            since: Only return papers published on or after this datetime.
            max_results: Maximum number of papers to return.
        """

    def _log(self, message: str) -> None:
        """Debug-level log (only with --debug)."""
        if self._debug and self._debug_log is not None:
            self._debug_log(message)

    def _progress(self, message: str) -> None:
        """Progress-level log (always visible)."""
        if self._progress_log is not None:
            self._progress_log(message)
        elif self._debug and self._debug_log is not None:
            self._debug_log(message)
