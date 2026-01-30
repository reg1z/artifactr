"""Vault catalog operations for Artifactr.

This module provides business logic for managing vaults, separate from CLI parsing.
"""

from pathlib import Path
from typing import Any

from .config import load_config, save_config


def add_vaults(paths: list[str]) -> dict[str, Any]:
    """Add one or more directories to the vault catalog.

    Args:
        paths: List of directory paths to add as vaults.

    Returns:
        Result dict with keys:
            - added: List of paths that were successfully added
            - skipped: List of paths that were already in the catalog
            - errors: List of error messages for invalid paths
    """
    config = load_config()
    existing_vaults = set(config["vaults"])

    added: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    for path_str in paths:
        path = Path(path_str).resolve()
        path_str_resolved = str(path)

        # Validate path exists and is a directory
        if not path.exists():
            errors.append(f"Path does not exist: {path_str}")
            continue
        if not path.is_dir():
            errors.append(f"Path is not a directory: {path_str}")
            continue

        # Check for duplicates
        if path_str_resolved in existing_vaults:
            skipped.append(path_str_resolved)
            continue

        # Add to catalog
        config["vaults"].append(path_str_resolved)
        existing_vaults.add(path_str_resolved)
        added.append(path_str_resolved)

    # Set first added vault as default if no default exists
    if added and config["default_vault"] is None:
        config["default_vault"] = added[0]

    save_config(config)

    return {"added": added, "skipped": skipped, "errors": errors}


def remove_vaults(paths: list[str]) -> dict[str, Any]:
    """Remove one or more directories from the vault catalog.

    Args:
        paths: List of vault paths to remove.

    Returns:
        Result dict with keys:
            - removed: List of paths that were successfully removed
            - not_found: List of paths that were not in the catalog
    """
    config = load_config()

    removed: list[str] = []
    not_found: list[str] = []

    for path_str in paths:
        path = Path(path_str).resolve()
        path_str_resolved = str(path)

        if path_str_resolved in config["vaults"]:
            config["vaults"].remove(path_str_resolved)
            removed.append(path_str_resolved)

            # Clear default if the removed vault was the default
            if config["default_vault"] == path_str_resolved:
                config["default_vault"] = None
        else:
            not_found.append(path_str)

    save_config(config)

    return {"removed": removed, "not_found": not_found}


def select_default(path: str) -> bool:
    """Set a vault as the default.

    Args:
        path: Path to the vault to set as default.

    Returns:
        True if successful, False if the vault is not in the catalog.
    """
    config = load_config()
    resolved_path = str(Path(path).resolve())

    if resolved_path not in config["vaults"]:
        return False

    config["default_vault"] = resolved_path
    save_config(config)
    return True


def list_vaults() -> dict[str, Any]:
    """List all vaults in the catalog.

    Returns:
        Dict with keys:
            - vaults: List of all registered vault paths
            - default: Path of the default vault, or None if not set
    """
    config = load_config()
    return {"vaults": config["vaults"], "default": config["default_vault"]}


def get_default_vault() -> str | None:
    """Get the default vault path.

    Returns:
        The default vault path, or None if not set.
    """
    config = load_config()
    return config["default_vault"]


def get_vault_by_name_or_path(identifier: str) -> str | None:
    """Find a vault by exact path or by basename.

    Args:
        identifier: Either a full path or the basename of a vault directory.

    Returns:
        The full vault path if found in catalog, None otherwise.
    """
    config = load_config()
    resolved_identifier = str(Path(identifier).resolve())

    # First, try exact path match
    if resolved_identifier in config["vaults"]:
        return resolved_identifier

    # Then, try basename match
    for vault_path in config["vaults"]:
        vault_basename = Path(vault_path).name
        if vault_basename == identifier:
            return vault_path

    return None


def select_default_tool(tool_name: str, supported_tools: list[str]) -> bool:
    """Set a tool as the default.

    Args:
        tool_name: Name of the tool to set as default.
        supported_tools: List of supported tool names for validation.

    Returns:
        True if successful, False if the tool is not supported.
    """
    if tool_name not in supported_tools:
        return False

    config = load_config()
    config["default_tool"] = tool_name
    save_config(config)
    return True


def get_default_tool() -> str:
    """Get the default tool name.

    Returns:
        The default tool name.
    """
    config = load_config()
    return config["default_tool"]


def list_tools_info(supported_tools: list[str]) -> dict[str, Any]:
    """Get information about tools and current default.

    Args:
        supported_tools: List of supported tool names.

    Returns:
        Dict with keys:
            - tools: List of all supported tool names
            - default: Name of the default tool
    """
    config = load_config()
    return {"tools": supported_tools, "default": config["default_tool"]}
