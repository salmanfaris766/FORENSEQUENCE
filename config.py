# -*- coding: utf-8 -*-
"""
config.py
Configuration manager for FORENSEQUENCE GUI application.

Provides persistent JSON settings stored in `config.json` at the repository root.
Default values are defined in `DEFAULTS`. The manager reads the file on first
access, merges with defaults, and writes atomically using a temporary `.tmp`
file to avoid corruption.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

# Default configuration values
DEFAULTS: Dict[str, Any] = {
    "default_investigator": "Salman",
    "auto_run_analysis": True,
    "live_poll_interval_ms": 200,
    "export_directory": "uploads",
    "toast_duration_ms": 5000,
}

# Path to the JSON file (located at repository root)
CONFIG_JSON_PATH = Path(__file__).with_name("config.json")


class ConfigManager:
    """
    Utility class for reading and writing application settings.

    All methods are class methods so the manager can be used without instantiating
    an object. The internal cache stores the merged configuration after the
    first load.
    """

    _cache: Dict[str, Any] | None = None

    @classmethod
    def _load(cls) -> Dict[str, Any]:
        """Load configuration from disk, merging with `DEFAULTS`."""
        if cls._cache is not None:
            return cls._cache
        if CONFIG_JSON_PATH.is_file():
            try:
                with CONFIG_JSON_PATH.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
            except Exception:
                data = {}
        else:
            data = {}
        merged = {**DEFAULTS, **data}
        cls._cache = merged
        return merged

    @classmethod
    def _write(cls, payload: Dict[str, Any]) -> None:
        """Write payload atomically to `config.json`."""
        tmp_path = CONFIG_JSON_PATH.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, sort_keys=True)
        tmp_path.replace(CONFIG_JSON_PATH)
        cls._cache = None

    @classmethod
    def get(cls, key: str) -> Any:
        """Return the value for key in the configuration."""
        cfg = cls._load()
        return cfg.get(key)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Set value for key and persist the change."""
        cfg = cls._load()
        cfg[key] = value
        cls._write(cfg)

    @classmethod
    def as_dict(cls) -> Dict[str, Any]:
        """Return a shallow copy of the entire configuration dictionary."""
        return dict(cls._load())

    @classmethod
    def reset_to_defaults(cls) -> None:
        """Overwrite `config.json` with the default settings."""
        cls._write(dict(DEFAULTS))
