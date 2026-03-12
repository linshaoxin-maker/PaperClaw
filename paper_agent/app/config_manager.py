"""Configuration management: load, save, validate YAML config."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from paper_agent.domain.exceptions import (
    ConfigurationNotFoundError,
    ConfigurationValidationError,
)

DEFAULT_DATA_DIR = Path.home() / ".paper-agent"
DEFAULT_CONFIG_PATH = DEFAULT_DATA_DIR / "config.yaml"
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "library.db"
DEFAULT_ARTIFACTS_DIR = DEFAULT_DATA_DIR / "artifacts"

_REQUIRED_FIELDS = ["topics", "sources", "llm_provider"]


@dataclass
class ConfigProfile:
    topics: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=lambda: ["cs.AI", "cs.LG"])
    llm_provider: str = "anthropic"
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = ""
    digest_top_n: int = 20
    relevance_threshold: float = 5.0
    data_dir: str = str(DEFAULT_DATA_DIR)
    db_path: str = str(DEFAULT_DB_PATH)
    artifacts_dir: str = str(DEFAULT_ARTIFACTS_DIR)

    def to_dict(self, mask_api_key: bool = True) -> dict[str, Any]:
        api_key_display = self.llm_api_key
        if mask_api_key and self.llm_api_key:
            # Show first 8 and last 4 characters, mask the middle
            if len(self.llm_api_key) > 12:
                api_key_display = f"{self.llm_api_key[:8]}...{self.llm_api_key[-4:]}"
            else:
                api_key_display = f"{self.llm_api_key[:4]}...{self.llm_api_key[-2:]}"

        d = {
            "topics": self.topics,
            "keywords": self.keywords,
            "sources": self.sources,
            "llm_provider": self.llm_provider,
            "llm_api_key": api_key_display,
            "llm_model": self.llm_model,
            "llm_base_url": self.llm_base_url,
            "digest_top_n": self.digest_top_n,
            "relevance_threshold": self.relevance_threshold,
            "data_dir": self.data_dir,
            "db_path": self.db_path,
            "artifacts_dir": self.artifacts_dir,
        }
        return d


class ConfigManager:
    def __init__(self, config_path: str | Path | None = None) -> None:
        self._config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    @property
    def config_path(self) -> Path:
        return self._config_path

    def is_initialized(self) -> bool:
        return self._config_path.exists()

    def load_config(self) -> ConfigProfile:
        if not self._config_path.exists():
            raise ConfigurationNotFoundError(
                f"配置文件不存在: {self._config_path}。请先执行 paper-agent init。"
            )
        with open(self._config_path) as f:
            raw = yaml.safe_load(f) or {}
        return self._dict_to_profile(raw)

    def save_config(self, config: ConfigProfile) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        # Save with full API key (no masking)
        data = config.to_dict(mask_api_key=False)
        with open(self._config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def validate_config(self, config: ConfigProfile) -> list[str]:
        errors: list[str] = []
        if not config.topics:
            errors.append("缺少 topics（研究方向）")
        if not config.sources:
            errors.append("缺少 sources（论文来源）")
        if not config.llm_provider:
            errors.append("缺少 llm_provider（LLM 提供商）")
        return errors

    def ensure_dirs(self, config: ConfigProfile) -> None:
        Path(config.data_dir).mkdir(parents=True, exist_ok=True)
        Path(config.artifacts_dir).mkdir(parents=True, exist_ok=True)

    def _dict_to_profile(self, raw: dict[str, Any]) -> ConfigProfile:
        import os

        profile = ConfigProfile(
            topics=raw.get("topics", []),
            keywords=raw.get("keywords", []),
            sources=raw.get("sources", ["cs.AI", "cs.LG"]),
            llm_provider=raw.get("llm_provider", "anthropic"),
            llm_api_key=os.environ.get("PAPER_AGENT_LLM_API_KEY", raw.get("llm_api_key", "")),
            llm_model=raw.get("llm_model", ""),
            llm_base_url=raw.get("llm_base_url", ""),
            digest_top_n=raw.get("digest_top_n", 20),
            relevance_threshold=raw.get("relevance_threshold", 5.0),
            data_dir=raw.get("data_dir", str(DEFAULT_DATA_DIR)),
            db_path=raw.get("db_path", str(DEFAULT_DB_PATH)),
            artifacts_dir=raw.get("artifacts_dir", str(DEFAULT_ARTIFACTS_DIR)),
        )
        return profile
