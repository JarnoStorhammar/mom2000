from pathlib import Path; import os, yaml

def load_config(path=None) -> dict:
    p = Path(path or os.getenv("CONFIG_PATH","config/config.yaml"))
    if not p.exists(): return {}
    with open(p) as f: return yaml.safe_load(f) or {}
