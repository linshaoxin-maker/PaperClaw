"""Source registry.

Loads built-in sources from `sources.yaml` (repo) and merges a user override layer
stored under the user's data dir (default: ~/.paper-agent/sources.yaml).

This module defines v01_source's first-class "Source" concept.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


@dataclass(frozen=True)
class SourceDefinition:
    id: str
    type: str
    display_name: str
    description: str = ""
    api_type: str = ""
    api_config: dict[str, Any] | None = None
    enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "display_name": self.display_name,
            "description": self.description,
            "api_type": self.api_type,
            "api_config": self.api_config or {},
            "enabled": self.enabled,
        }


class UnknownSourceError(ValueError):
    pass


class SourceRegistry:
    """Registry for all sources (built-in + user custom/overrides)."""

    def __init__(
        self,
        *,
        builtin_sources_path: str | Path | None = None,
        user_sources_path: str | Path | None = None,
    ) -> None:
        self._builtin_sources_path = (
            Path(builtin_sources_path)
            if builtin_sources_path
            else Path(__file__).with_name("sources.yaml")
        )
        self._user_sources_path = Path(user_sources_path) if user_sources_path else None

        self._raw_builtin: dict[str, Any] = {}
        self._raw_user: dict[str, Any] = {}
        self._sources_by_id: dict[str, SourceDefinition] = {}
        self._templates: dict[str, dict[str, Any]] = {}

        self.reload()

    @property
    def builtin_sources_path(self) -> Path:
        return self._builtin_sources_path

    @property
    def user_sources_path(self) -> Path | None:
        return self._user_sources_path

    def reload(self) -> None:
        self._raw_builtin = self._load_yaml(self._builtin_sources_path)
        self._raw_user = self._load_yaml(self._user_sources_path) if self._user_sources_path else {}

        self._templates = dict(self._raw_builtin.get("research_area_templates", {}) or {})
        self._sources_by_id = self._build_sources_index()

    def list_sources(self) -> list[SourceDefinition]:
        return sorted(self._sources_by_id.values(), key=lambda s: s.id)

    def get_source(self, source_id: str) -> SourceDefinition:
        try:
            return self._sources_by_id[source_id]
        except KeyError as e:
            raise UnknownSourceError(f"Unknown source id: {source_id}") from e

    def list_enabled_sources(self) -> list[SourceDefinition]:
        return [s for s in self.list_sources() if s.enabled]

    def list_research_area_templates(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for tid, t in sorted(self._templates.items(), key=lambda kv: kv[0]):
            items.append({"id": tid, **(t or {})})
        return items

    def get_research_area_template(self, template_id: str) -> dict[str, Any]:
        if template_id not in self._templates:
            raise KeyError(f"Unknown research area template: {template_id}")
        return {"id": template_id, **(self._templates[template_id] or {})}

    def enable(self, source_ids: Iterable[str]) -> None:
        self._update_override(enabled_add=set(source_ids), disabled_add=set())

    def disable(self, source_ids: Iterable[str]) -> None:
        self._update_override(enabled_add=set(), disabled_add=set(source_ids))

    def add_custom(self, source: dict[str, Any]) -> None:
        """Add a custom source definition to user override file.

        The custom source format is intentionally flexible for MVP.
        Required keys: id, name (or display_name), type
        """

        source_id = str(source.get("id", "")).strip()
        if not source_id:
            raise ValueError("custom source missing 'id'")

        user = self._raw_user or {}
        custom_sources = list(user.get("custom_sources", []) or [])
        custom_sources.append(source)
        user["custom_sources"] = custom_sources
        self._raw_user = user
        self._persist_user_override()
        self.reload()

    def recommend_for_template(self, template_id: str) -> list[str]:
        """Return recommended source IDs for a research area template.

        This provides the deterministic rule-based recommendation used by profile.
        """

        template = self.get_research_area_template(template_id)
        rec = template.get("recommended_sources", {}) or {}

        ids: list[str] = []

        for cat in rec.get("arxiv", []) or []:
            ids.append(f"arxiv:{cat}")

        for conf_key in rec.get("conferences", []) or []:
            ids.append(f"conf:{conf_key}")

        # Filter to known ids
        return [i for i in ids if i in self._sources_by_id]

    # -----------------
    # Internal helpers
    # -----------------

    def _build_sources_index(self) -> dict[str, SourceDefinition]:
        # User overrides
        enabled_ids = set(self._raw_user.get("enabled", []) or [])
        disabled_ids = set(self._raw_user.get("disabled", []) or [])

        by_id: dict[str, SourceDefinition] = {}

        # arXiv categories
        for cat, meta in (self._raw_builtin.get("arxiv_categories", {}) or {}).items():
            meta = meta or {}
            source_id = f"arxiv:{cat}"
            default_enabled = False
            enabled = self._resolve_enabled(source_id, default_enabled, enabled_ids, disabled_ids)
            by_id[source_id] = SourceDefinition(
                id=source_id,
                type="arxiv_category",
                display_name=f"arXiv {cat}",
                description=str(meta.get("description", "")),
                api_type="arxiv",
                api_config={"category": cat},
                enabled=enabled,
            )

        # conferences
        for conf_key, conf in (self._raw_builtin.get("conferences", {}) or {}).items():
            conf = conf or {}
            source_id = f"conf:{conf_key}"
            default_enabled = bool(conf.get("enabled", False))
            enabled = self._resolve_enabled(source_id, default_enabled, enabled_ids, disabled_ids)
            by_id[source_id] = SourceDefinition(
                id=source_id,
                type="conference",
                display_name=str(conf.get("name", conf_key)),
                description=str(conf.get("full_name", "")),
                api_type=str(conf.get("api_type", "")),
                api_config=dict(conf.get("api_config", {}) or {}),
                enabled=enabled,
            )

        # other sources (top-level providers)
        for other_key, other in (self._raw_builtin.get("other_sources", {}) or {}).items():
            other = other or {}
            source_id = f"other:{other_key}"
            default_enabled = bool(other.get("enabled", False))
            enabled = self._resolve_enabled(source_id, default_enabled, enabled_ids, disabled_ids)
            by_id[source_id] = SourceDefinition(
                id=source_id,
                type="other",
                display_name=str(other.get("name", other_key)),
                description=str(other.get("description", "")),
                api_type=str(other.get("api_type", "")),
                api_config={},
                enabled=enabled,
            )

        # custom sources (user)
        for custom in (self._raw_user.get("custom_sources", []) or []):
            if not isinstance(custom, dict):
                continue
            cid = str(custom.get("id", "")).strip()
            if not cid:
                continue
            source_id = f"custom:{cid}" if ":" not in cid else cid
            default_enabled = bool(custom.get("enabled", True))
            enabled = self._resolve_enabled(source_id, default_enabled, enabled_ids, disabled_ids)
            by_id[source_id] = SourceDefinition(
                id=source_id,
                type=str(custom.get("type", "custom")),
                display_name=str(custom.get("name", custom.get("display_name", cid))),
                description=str(custom.get("description", "")),
                api_type=str(custom.get("api_type", "")),
                api_config=dict(custom.get("api_config", {}) or {}),
                enabled=enabled,
            )

        return by_id

    def _resolve_enabled(
        self,
        source_id: str,
        default_enabled: bool,
        enabled_ids: set[str],
        disabled_ids: set[str],
    ) -> bool:
        if source_id in enabled_ids:
            return True
        if source_id in disabled_ids:
            return False
        return default_enabled

    def _update_override(self, *, enabled_add: set[str], disabled_add: set[str]) -> None:
        # Validate ids exist (or are custom). For MVP, only enforce for known builtins.
        unknown = [sid for sid in (enabled_add | disabled_add) if sid not in self._sources_by_id]
        if unknown:
            raise UnknownSourceError(
                "Unknown source id(s): " + ", ".join(sorted(unknown))
            )

        user = self._raw_user or {}
        enabled = set(user.get("enabled", []) or [])
        disabled = set(user.get("disabled", []) or [])

        enabled |= enabled_add
        enabled -= disabled_add

        disabled |= disabled_add
        disabled -= enabled_add

        user["enabled"] = sorted(enabled)
        user["disabled"] = sorted(disabled)
        user.setdefault("custom_sources", user.get("custom_sources", []) or [])

        self._raw_user = user
        self._persist_user_override()
        self.reload()

    def _persist_user_override(self) -> None:
        if not self._user_sources_path:
            return
        self._user_sources_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "enabled": sorted(set(self._raw_user.get("enabled", []) or [])),
            "disabled": sorted(set(self._raw_user.get("disabled", []) or [])),
            "custom_sources": list(self._raw_user.get("custom_sources", []) or []),
        }

        with open(self._user_sources_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def _load_yaml(self, path: Path | None) -> dict[str, Any]:
        if not path:
            return {}
        if not path.exists():
            return {}
        with open(path) as f:
            loaded = yaml.safe_load(f) or {}
        if not isinstance(loaded, dict):
            return {}
        return loaded
