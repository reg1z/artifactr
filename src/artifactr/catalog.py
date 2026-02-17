"""Vault catalog operations for Artifactr.

This module provides business logic for managing vaults, separate from CLI parsing.
"""

import re
from pathlib import Path
from typing import Any

from .config import load_config, save_config


def _next_auto_name(config: dict[str, Any]) -> str:
    """Compute the next auto-name using the vault-N pattern."""
    max_n = 0
    for vault_name in config["vault_names"].values():
        m = re.match(r"^vault-(\d+)$", vault_name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"vault-{max_n + 1}"


def add_vaults(paths: list[str], name: str | None = None) -> dict[str, Any]:
    """Add one or more directories to the vault catalog.

    Args:
        paths: List of directory paths to add as vaults.
        name: Optional name for the vault (only used when adding a single path).
              If None, vaults are auto-named using the vault-N pattern.

    Returns:
        Result dict with keys:
            - added: List of paths that were successfully added
            - skipped: List of paths that were already in the catalog
            - errors: List of error messages for invalid paths
            - names: Dict mapping added paths to their assigned names
    """
    config = load_config()
    existing_vaults = set(config["vaults"])

    added: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []
    assigned_names: dict[str, str] = {}

    # Validate name uniqueness if provided
    if name is not None:
        for vault_path, existing_name in config["vault_names"].items():
            if existing_name == name:
                errors.append(
                    f"Vault name already in use: {name} (used by {vault_path}). "
                    f"Use 'art vault name {name} <new-name>' to rename it."
                )
                return {"added": added, "skipped": skipped, "errors": errors, "names": assigned_names}

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

        # Assign name
        if name is not None:
            # Explicit name for the first added vault only
            config["vault_names"][path_str_resolved] = name
            assigned_names[path_str_resolved] = name
        else:
            # Auto-name
            auto_name = _next_auto_name(config)
            config["vault_names"][path_str_resolved] = auto_name
            assigned_names[path_str_resolved] = auto_name

    # Set first added vault as default if no default exists
    if added and config["default_vault"] is None:
        config["default_vault"] = added[0]

    save_config(config)

    return {"added": added, "skipped": skipped, "errors": errors, "names": assigned_names}


def init_vault(target_dir: str, name: str | None = None) -> dict[str, Any]:
    """Initialize a new vault directory with scaffolding and register it.

    Creates the target directory with skills/, agents/, and commands/ subdirectories
    if it doesn't already exist. Then registers the vault via add_vaults().

    Args:
        target_dir: Path to the vault directory to create/register.
        name: Optional name for the vault (auto-named if None).

    Returns:
        Result dict with keys:
            - created: Whether the directory was newly created
            - added: List of paths that were added (from add_vaults)
            - skipped: List of paths already registered (from add_vaults)
            - errors: List of error messages
            - names: Dict mapping paths to assigned names
    """
    path = Path(target_dir).resolve()
    dir_missing = not path.exists()

    if not dir_missing:
        # Directory exists, just register it
        result = add_vaults([str(path)], name=name)
        result["created"] = False
        result["dir_missing"] = False
        return result

    # Directory doesn't exist — return signal for CLI to handle prompting
    result: dict[str, Any] = {
        "added": [],
        "skipped": [],
        "errors": [],
        "names": {},
        "created": False,
        "dir_missing": True,
        "target_path": str(path),
    }
    return result


def create_vault_directory(target_dir: str, name: str | None = None) -> dict[str, Any]:
    """Create the vault directory structure and register it.

    Called after user confirms directory creation (or with --yes).
    """
    path = Path(target_dir).resolve()
    path.mkdir(parents=True, exist_ok=True)
    (path / "skills").mkdir(exist_ok=True)
    (path / "agents").mkdir(exist_ok=True)
    (path / "commands").mkdir(exist_ok=True)

    result = add_vaults([str(path)], name=name)
    result["created"] = True
    result["dir_missing"] = False
    return result


def remove_vaults(paths: list[str]) -> dict[str, Any]:
    """Remove one or more directories from the vault catalog.

    Accepts vault names or paths as identifiers.

    Args:
        paths: List of vault paths or names to remove.

    Returns:
        Result dict with keys:
            - removed: List of paths that were successfully removed
            - not_found: List of identifiers that were not in the catalog
    """
    config = load_config()

    removed: list[str] = []
    not_found: list[str] = []

    for identifier in paths:
        # Resolve identifier to a vault path
        resolved = _resolve_vault_identifier(identifier, config)

        if resolved is not None and resolved in config["vaults"]:
            config["vaults"].remove(resolved)
            removed.append(resolved)

            # Clean up vault name
            config["vault_names"].pop(resolved, None)

            # Clear default if the removed vault was the default
            if config["default_vault"] == resolved:
                config["default_vault"] = None
        else:
            not_found.append(identifier)

    save_config(config)

    return {"removed": removed, "not_found": not_found}


def select_default(identifier: str) -> bool:
    """Set a vault as the default.

    Accepts a vault name or path as identifier.

    Args:
        identifier: Name or path of the vault to set as default.

    Returns:
        True if successful, False if the vault is not in the catalog.
    """
    config = load_config()
    resolved = _resolve_vault_identifier(identifier, config)

    if resolved is None or resolved not in config["vaults"]:
        return False

    config["default_vault"] = resolved
    save_config(config)
    return True


def list_vaults() -> dict[str, Any]:
    """List all vaults in the catalog.

    Returns:
        Dict with keys:
            - vaults: List of all registered vault paths
            - default: Path of the default vault, or None if not set
            - vault_names: Dict mapping vault paths to their names
    """
    config = load_config()
    return {
        "vaults": config["vaults"],
        "default": config["default_vault"],
        "vault_names": config["vault_names"],
    }


def get_default_vault() -> str | None:
    """Get the default vault path.

    Returns:
        The default vault path, or None if not set.
    """
    config = load_config()
    return config["default_vault"]


def get_vault_by_name_or_path(identifier: str) -> str | None:
    """Find a vault by name, exact path, or basename.

    Lookup order:
        1. Exact resolved path match
        2. Vault name match
        3. Directory basename match

    Args:
        identifier: A vault name, full path, or basename of a vault directory.

    Returns:
        The full vault path if found in catalog, None otherwise.
    """
    config = load_config()
    return _resolve_vault_identifier(identifier, config)


def _resolve_vault_identifier(identifier: str, config: dict[str, Any]) -> str | None:
    """Resolve a vault identifier to a full path using the given config.

    Args:
        identifier: A vault name, full path, or basename.
        config: The loaded configuration dict.

    Returns:
        The full vault path if found, None otherwise.
    """
    resolved_identifier = str(Path(identifier).resolve())

    # First, try exact path match
    if resolved_identifier in config["vaults"]:
        return resolved_identifier

    # Then, try vault name match
    for vault_path, vault_name in config["vault_names"].items():
        if vault_name == identifier:
            return vault_path

    # Finally, try basename match
    for vault_path in config["vaults"]:
        vault_basename = Path(vault_path).name
        if vault_basename == identifier:
            return vault_path

    return None


def name_vault(identifier: str, name: str) -> dict[str, Any]:
    """Set or change the name of a vault.

    Args:
        identifier: Name or path of the vault to name.
        name: The new name to assign.

    Returns:
        Result dict with keys:
            - success: Whether the operation succeeded
            - vault_path: The resolved vault path (if found)
            - error: Error message (if failed)
    """
    config = load_config()
    resolved = _resolve_vault_identifier(identifier, config)

    if resolved is None or resolved not in config["vaults"]:
        return {"success": False, "vault_path": None, "error": f"Vault not in catalog: {identifier}"}

    # Check name uniqueness (allow re-assigning the same name to the same vault)
    for vault_path, existing_name in config["vault_names"].items():
        if existing_name == name and vault_path != resolved:
            return {"success": False, "vault_path": resolved, "error": f"Name already in use by: {vault_path}"}

    config["vault_names"][resolved] = name
    save_config(config)

    return {"success": True, "vault_path": resolved, "error": None}


def get_vault_hierarchy(vault_path: str) -> dict | None:
    """Get the artifact hierarchy for a vault.

    Args:
        vault_path: Path to the vault directory.

    Returns:
        Dict mapping artifact types to lists of names, or None if path doesn't exist.
    """
    path = Path(vault_path)
    if not path.exists():
        return None

    hierarchy = {}
    for artifact_type in ["skills", "agents", "commands"]:
        type_path = path / artifact_type
        items = []
        if type_path.is_dir():
            for item in sorted(type_path.iterdir()):
                if artifact_type == "skills" and item.is_dir():
                    items.append(item.name)
                elif artifact_type in ("agents", "commands") and item.is_file() and item.suffix == ".md":
                    items.append(item.name)
        hierarchy[artifact_type] = items

    return hierarchy


def select_default_tool(tool_name: str, supported_tools: list[str]) -> bool:
    """Set a tool as the default. Resolves aliases before validation.

    Args:
        tool_name: Name of the tool to set as default.
        supported_tools: List of supported tool names for validation.

    Returns:
        True if successful, False if the tool is not supported.
    """
    from .tools import resolve_tool_name

    resolved = resolve_tool_name(tool_name)
    if resolved not in supported_tools:
        return False

    config = load_config()
    config["default_tool"] = resolved
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
