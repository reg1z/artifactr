"""Configuration loading and saving for Artifactr."""

from pathlib import Path
from typing import Any

import yaml

from .utils import get_config_dir


def get_config_path() -> Path:
    """Return the path to the configuration file."""
    return get_config_dir() / "config.yaml"


DEFAULT_TOOL = "opencode"


def load_config() -> dict[str, Any]:
    """Load the configuration from disk.

    Returns:
        Configuration dictionary with 'vaults', 'default_vault', 'default_tool',
        'vault_names', and 'tools' keys.
    """
    config_path = get_config_path()

    if not config_path.exists():
        return {
            "vaults": [],
            "default_vault": None,
            "default_tool": DEFAULT_TOOL,
            "vault_names": {},
            "tools": {},
        }

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if config is None:
        return {
            "vaults": [],
            "default_vault": None,
            "default_tool": DEFAULT_TOOL,
            "vault_names": {},
            "tools": {},
        }

    if "vaults" not in config:
        config["vaults"] = []
    if "default_vault" not in config:
        config["default_vault"] = None
    if "default_tool" not in config:
        config["default_tool"] = DEFAULT_TOOL
    if "vault_names" not in config:
        config["vault_names"] = {}
    if "tools" not in config:
        config["tools"] = {}

    return config


def save_config(config: dict[str, Any]) -> None:
    """Save the configuration to disk."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True)


def load_global_tools() -> dict[str, dict]:
    """Load user-defined tools from the global config file.

    Returns:
        Dict of tool name -> tool definition from the 'tools' section.
    """
    config = load_config()
    return config.get("tools", {})


def save_global_tools(tools: dict[str, dict]) -> None:
    """Save user-defined tools to the global config file."""
    config = load_config()
    config["tools"] = tools
    save_config(config)


def load_vault_metadata(vault_path: str | Path) -> dict[str, Any]:
    """Read vault.yaml from a vault directory.

    Returns dict with 'name' and 'tools' keys (empty defaults if file missing).
    """
    meta_path = Path(vault_path) / "vault.yaml"
    if not meta_path.exists():
        return {"name": None, "tools": {}}

    with open(meta_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        return {"name": None, "tools": {}}

    return {
        "name": data.get("name"),
        "tools": data.get("tools", {}),
    }


def load_active_vault_tools() -> tuple[dict[str, dict], str | None]:
    """Load tool definitions from the default vault.

    Returns:
        Tuple of (tools_dict, vault_name). Returns ({}, None) if no default vault.
    """
    from .catalog import get_default_vault

    default_vault = get_default_vault()
    if default_vault is None:
        return {}, None

    meta = load_vault_metadata(default_vault)
    return meta.get("tools", {}), meta.get("name")


def load_all_vault_tools() -> list[tuple[str | None, str, dict[str, dict]]]:
    """Iterate all registered vaults and collect their tool definitions.

    Returns:
        List of (vault_name, vault_path, tools_dict) tuples.
    """
    from .catalog import list_vaults

    info = list_vaults()
    result = []
    for vault_path in info["vaults"]:
        meta = load_vault_metadata(vault_path)
        vault_name = meta.get("name") or info["vault_names"].get(vault_path)
        result.append((vault_name, vault_path, meta.get("tools", {})))
    return result


def load_cwd_vault_tools() -> dict[str, dict]:
    """Read tool definitions from a vault.yaml in the current working directory.

    Returns:
        Tools dict from ./vault.yaml, or empty dict if not present.
    """
    meta_path = Path.cwd() / "vault.yaml"
    if not meta_path.exists():
        return {}

    with open(meta_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        return {}

    return data.get("tools", {}) or {}


def save_vault_metadata(vault_path: str | Path, metadata: dict[str, Any]) -> None:
    """Write vault.yaml to a vault directory."""
    meta_path = Path(vault_path) / "vault.yaml"

    # Build output dict, omitting None name
    output: dict[str, Any] = {}
    if metadata.get("name") is not None:
        output["name"] = metadata["name"]
    if metadata.get("tools"):
        output["tools"] = metadata["tools"]

    with open(meta_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(output, f, default_flow_style=False, allow_unicode=True)
