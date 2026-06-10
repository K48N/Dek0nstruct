"""Dek0nstruct runtime configuration."""
import os
import json
import copy
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

APP_DATA = os.getenv("APPDATA") or os.path.expanduser("~/.local/share")
APP_CONFIG_DIR = Path(APP_DATA) / "Dek0nstruct"
CONFIG_FILE = APP_CONFIG_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "app": {
        "debug_mode": False,
    },
    "cache": {
        "max_size_gb": 10,
        "max_age_days": 30,
        "thumbnail_interval": 1.0,
    },
    "export": {
        "max_concurrent_jobs": 2,
        "default_format": "mp4",
        "temp_directory": None,
    },
}


class RuntimeConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self._cfg: Dict[str, Any] = copy.deepcopy(DEFAULT_CONFIG)
        APP_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if CONFIG_FILE.exists():
            try:
                with CONFIG_FILE.open() as f:
                    self._merge(self._cfg, json.load(f))
            except Exception as e:
                logger.warning("Could not load config: %s", e)
        if not self._cfg["export"]["temp_directory"]:
            self._cfg["export"]["temp_directory"] = str(APP_CONFIG_DIR / "temp")
        Path(self._cfg["export"]["temp_directory"]).mkdir(parents=True, exist_ok=True)
        self.save()

    def _merge(self, base: dict, update: dict):
        for k, v in update.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._merge(base[k], v)
            else:
                base[k] = v

    def get(self, section: str, key: str = None):
        if key is None:
            return self._cfg.get(section, {})
        return self._cfg.get(section, {}).get(key)

    def set(self, section: str, key: str, value: Any):
        self._cfg.setdefault(section, {})[key] = value

    def save(self):
        try:
            CONFIG_FILE.write_text(json.dumps(self._cfg, indent=2))
        except Exception as e:
            logger.warning("Could not save config: %s", e)


config = RuntimeConfig()
