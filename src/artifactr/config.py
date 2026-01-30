"""Configuration loading and saving for Artifactr."""

from pathlib import Path
from typing import Any

import yaml

from .utils import get_config_dir


def get_config_path() -> Path:
    """Return the path to the configuration file.

    Returns:
        Path to config.yaml within the platform-specific config directory.
    """
    return get_config_dir() / "config.yaml"


DEFAULT_TOOL = "opencode"


def load_config() -> dict[str, Any]:
    """Load the configuration from disk.

    Returns:
        Configuration dictionary with 'vaults' list, 'default_vault', and 'default_tool' keys.
        If the config file doesn't exist, returns a default empty config.
    """
    config_path = get_config_path()

    if not config_path.exists():
        return {"vaults": [], "default_vault": None, "default_tool": DEFAULT_TOOL}

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Handle empty file or invalid YAML
    if config is None:
        return {"vaults": [], "default_vault": None, "default_tool": DEFAULT_TOOL}

    # Ensure required keys exist with proper defaults
    if "vaults" not in config:
        config["vaults"] = []
    if "default_vault" not in config:
        config["default_vault"] = None
    if "default_tool" not in config:
        config["default_tool"] = DEFAULT_TOOL

    return config


def save_config(config: dict[str, Any]) -> None:
    """Save the configuration to disk.

    Creates parent directories if they don't exist.

    Args:
        config: Configuration dictionary to save.
    """
    config_path = get_config_path()

    # Create parent directories if needed
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True)
