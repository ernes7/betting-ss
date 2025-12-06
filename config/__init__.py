"""Configuration module - pure dict access to YAML settings."""

import yaml
from pathlib import Path

_config_dir = Path(__file__).parent

# Load settings
with open(_config_dir / "settings.yaml") as f:
    settings = yaml.safe_load(f)

# Load URLs
with open(_config_dir / "urls.yaml") as f:
    urls = yaml.safe_load(f)

__all__ = ["settings", "urls"]
