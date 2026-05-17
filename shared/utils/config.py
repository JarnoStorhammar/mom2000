"""Load config.yaml with environment variable overrides."""
from __future__ import annotations
import os
from pathlib import Path
import yaml

def load_config(path: str | None = None) -> dict:
    cfg_path = Path(path or os.getenv("CONFIG_PATH", "config/config.yaml"))
    if not cfg_path.exists():
        return {}
    with open(cfg_path) as f:
        return yaml.safe_load(f) or {}
