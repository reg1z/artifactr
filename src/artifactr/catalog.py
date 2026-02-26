"""Vault catalog operations for Artifactr.

This module provides business logic for managing vaults, separate from CLI parsing.
"""

import fnmatch
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

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


# ---------------------------------------------------------------------------
# Vault copy
# ---------------------------------------------------------------------------

_VAULT_ARTIFACT_DIRS = ("skills", "commands", "agents")


def copy_vault(
    source: str,
    dest: str,
    copy_all: bool = False,
) -> dict[str, Any]:
    """Copy a vault to a new location and auto-register the copy.

    Args:
        source: Source vault name or path.
        dest: Destination path or plain name (no path separator → fallback location).
        copy_all: If True, copy all vault contents except .git/. Default: artifact dirs + vault.yaml only.

    Returns:
        Result dict with keys:
            - success: bool
            - dest_path: str destination path (if success)
            - name: str vault name assigned
            - error: str | None
    """
    from .config import get_config_dir, load_vault_metadata, save_vault_metadata

    config = load_config()
    source_path = _resolve_vault_identifier(source, config)
    if source_path is None:
        # Try direct filesystem path
        p = Path(source).resolve()
        if p.is_dir():
            source_path = str(p)
        else:
            return {"success": False, "dest_path": None, "name": None, "error": f"Source vault not found: {source}"}

    source_dir = Path(source_path)

    # Resolve destination
    if "/" in dest or "\\" in dest or dest.startswith(".") or dest.startswith("~"):
        dest_dir = Path(dest).expanduser().resolve()
        vault_name = dest_dir.name
    else:
        # Plain name → fallback location
        vault_name = dest
        dest_dir = get_config_dir() / "vaults" / dest

    if dest_dir.exists():
        return {"success": False, "dest_path": None, "name": None, "error": f"Destination already exists: {dest_dir}"}

    dest_dir.mkdir(parents=True)

    if copy_all:
        # Copy everything except .git/
        for item in source_dir.iterdir():
            if item.name == ".git":
                continue
            dest_item = dest_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest_item)
            else:
                shutil.copy2(item, dest_item)
    else:
        # Copy only artifact dirs and vault.yaml
        for dirname in _VAULT_ARTIFACT_DIRS:
            src_sub = source_dir / dirname
            if src_sub.is_dir():
                shutil.copytree(src_sub, dest_dir / dirname)
        src_yaml = source_dir / "vault.yaml"
        if src_yaml.exists():
            shutil.copy2(src_yaml, dest_dir / "vault.yaml")

    # Update vault.yaml with new name
    meta = load_vault_metadata(dest_dir)
    meta["name"] = vault_name
    save_vault_metadata(dest_dir, meta)

    # Auto-register
    reg_result = add_vaults([str(dest_dir)], name=vault_name)

    return {
        "success": True,
        "dest_path": str(dest_dir),
        "name": vault_name,
        "error": None,
        "registration": reg_result,
    }


# ---------------------------------------------------------------------------
# Vault export
# ---------------------------------------------------------------------------

def export_vaults(
    vault_paths: list[str],
    vault_names: list[str],
    output_path: str,
) -> dict[str, Any]:
    """Export vaults to a zip archive with manifest.yaml.

    Args:
        vault_paths: List of absolute vault directory paths to export.
        vault_names: Corresponding names for each vault (parallel list).
        output_path: Path for the output .zip file.

    Returns:
        Result dict with keys:
            - success: bool
            - output: str output path (if success)
            - error: str | None
    """
    out = Path(output_path)
    if out.exists():
        return {"success": False, "output": None, "error": f"Output file already exists: {output_path}"}

    manifest_entries = []

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for vault_path, vault_name in zip(vault_paths, vault_names):
            dir_name = vault_name
            manifest_entries.append({"name": vault_name, "dir": dir_name})
            vault_dir = Path(vault_path)

            # Write artifact dirs and vault.yaml
            for item_name in (*_VAULT_ARTIFACT_DIRS, "vault.yaml"):
                item = vault_dir / item_name
                if item.is_dir():
                    for file in item.rglob("*"):
                        if file.is_file():
                            arcname = f"{dir_name}/{item_name}/{file.relative_to(item)}"
                            zf.write(file, arcname)
                elif item.is_file():
                    zf.write(item, f"{dir_name}/{item_name}")

        # Write manifest.yaml
        manifest_yaml = yaml.dump({"vaults": manifest_entries}, default_flow_style=False)
        zf.writestr("manifest.yaml", manifest_yaml)

    return {"success": True, "output": str(out), "error": None}


def resolve_vaults_for_export(
    vaults_spec: str | None,
    export_all: bool,
) -> dict[str, Any]:
    """Resolve vault paths and names for export given a spec string.

    Args:
        vaults_spec: Comma-separated vault names or a single glob pattern. None if --all.
        export_all: If True, select all registered vaults.

    Returns:
        Result dict with keys:
            - success: bool
            - vault_paths: list[str]
            - vault_names: list[str]
            - error: str | None
    """
    config = load_config()

    if export_all:
        paths = config["vaults"]
        names = [config["vault_names"].get(p, Path(p).name) for p in paths]
        return {"success": True, "vault_paths": paths, "vault_names": names, "error": None}

    if vaults_spec is None:
        return {"success": False, "vault_paths": [], "vault_names": [], "error": "No vault specified. Provide vault names or use --all."}

    # Try comma-separated first
    if "," in vaults_spec:
        specs = [s.strip() for s in vaults_spec.split(",")]
    else:
        specs = [vaults_spec.strip()]

    # Check if it's a glob pattern (single spec with wildcard)
    all_names = {config["vault_names"].get(p, Path(p).name): p for p in config["vaults"]}

    selected_paths: list[str] = []
    selected_names: list[str] = []

    if len(specs) == 1 and any(c in specs[0] for c in ("*", "?", "[")):
        # Glob pattern
        pattern = specs[0]
        for name, path in all_names.items():
            if fnmatch.fnmatch(name, pattern):
                selected_paths.append(path)
                selected_names.append(name)
        if not selected_paths:
            return {"success": False, "vault_paths": [], "vault_names": [], "error": f"No vaults match pattern: {pattern}"}
    else:
        for spec in specs:
            resolved = _resolve_vault_identifier(spec, config)
            if resolved is None:
                return {"success": False, "vault_paths": [], "vault_names": [], "error": f"Vault not found: {spec}"}
            name = config["vault_names"].get(resolved, Path(resolved).name)
            selected_paths.append(resolved)
            selected_names.append(name)

    return {"success": True, "vault_paths": selected_paths, "vault_names": selected_names, "error": None}


# ---------------------------------------------------------------------------
# Vault import
# ---------------------------------------------------------------------------

def import_vaults_from_zip(
    archive_path: str,
    dest_dir: str | None,
) -> dict[str, Any]:
    """Extract vaults from a zip archive and register them.

    Args:
        archive_path: Path to the .zip archive.
        dest_dir: Directory to extract into. None → config_dir/vaults/.

    Returns:
        Result dict with keys:
            - success: bool
            - extracted: list[dict] with name, path for each vault
            - errors: list[str] per-vault errors
            - dest: str destination directory used
            - error: str | None (fatal errors only)
    """
    from .config import get_config_dir

    arc = Path(archive_path)
    if not arc.exists() or not arc.is_file():
        return {"success": False, "extracted": [], "errors": [], "dest": None, "error": f"Archive not found: {archive_path}"}

    try:
        if not zipfile.is_zipfile(arc):
            return {"success": False, "extracted": [], "errors": [], "dest": None, "error": f"Not a valid zip archive: {archive_path}"}
    except OSError as e:
        return {"success": False, "extracted": [], "errors": [], "dest": None, "error": str(e)}

    with zipfile.ZipFile(arc, "r") as zf:
        names_in_zip = zf.namelist()
        if "manifest.yaml" not in names_in_zip:
            return {"success": False, "extracted": [], "errors": [], "dest": None, "error": "Archive does not contain manifest.yaml"}

        manifest_data = yaml.safe_load(zf.read("manifest.yaml").decode("utf-8"))

    if not manifest_data or "vaults" not in manifest_data:
        return {"success": False, "extracted": [], "errors": [], "dest": None, "error": "manifest.yaml is invalid or missing 'vaults' key"}

    if dest_dir is None:
        dest = get_config_dir() / "vaults"
    else:
        dest = Path(dest_dir).expanduser().resolve()

    dest.mkdir(parents=True, exist_ok=True)

    extracted: list[dict[str, Any]] = []
    errors: list[str] = []

    config = load_config()

    with zipfile.ZipFile(arc, "r") as zf:
        for entry in manifest_data["vaults"]:
            vault_name = entry.get("name")
            vault_dir_name = entry.get("dir", vault_name)
            vault_dest = dest / vault_dir_name

            # Check for conflicts
            if str(vault_dest.resolve()) in config["vaults"]:
                errors.append(f"Path conflict: {vault_dest} already registered")
                continue
            for existing_path, existing_name in config["vault_names"].items():
                if existing_name == vault_name:
                    errors.append(f"Name conflict: '{vault_name}' already registered (path: {existing_path})")
                    break
            else:
                # Extract vault directory
                prefix = f"{vault_dir_name}/"
                for member in zf.infolist():
                    if member.filename.startswith(prefix):
                        rel = member.filename[len(prefix):]
                        if not rel:
                            continue
                        target = vault_dest / rel
                        if member.filename.endswith("/"):
                            target.mkdir(parents=True, exist_ok=True)
                        else:
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_bytes(zf.read(member.filename))

                # Register
                reg = add_vaults([str(vault_dest)], name=vault_name)
                if reg["errors"]:
                    errors.extend(reg["errors"])
                else:
                    extracted.append({"name": vault_name, "path": str(vault_dest)})

    return {
        "success": True,
        "extracted": extracted,
        "errors": errors,
        "dest": str(dest),
        "error": None,
    }


# ---------------------------------------------------------------------------
# Backup and restore
# ---------------------------------------------------------------------------

def backup_catalog(output_path: str) -> dict[str, Any]:
    """Create a backup archive of all registered vaults plus a config snapshot.

    Args:
        output_path: Path for the output .zip file.

    Returns:
        Result dict with keys:
            - success: bool
            - output: str output path (if success)
            - vault_count: int number of vaults backed up
            - error: str | None
    """
    out = Path(output_path)
    if out.exists():
        return {"success": False, "output": None, "vault_count": 0, "error": f"Output file already exists: {output_path}"}

    config = load_config()
    vault_paths = config["vaults"]
    vault_names = [config["vault_names"].get(p, Path(p).name) for p in vault_paths]

    # Determine default_vault_name (name, not path)
    default_vault = config.get("default_vault")
    default_vault_name: str | None = None
    if default_vault and default_vault in config["vault_names"]:
        default_vault_name = config["vault_names"][default_vault]
    elif default_vault:
        default_vault_name = Path(default_vault).name

    created_at = datetime.now(timezone.utc).isoformat()

    manifest_entries = []

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for vault_path, vault_name in zip(vault_paths, vault_names):
            dir_name = vault_name
            manifest_entries.append({"name": vault_name, "dir": dir_name})
            vault_dir = Path(vault_path)

            for item_name in (*_VAULT_ARTIFACT_DIRS, "vault.yaml"):
                item = vault_dir / item_name
                if item.is_dir():
                    for file in item.rglob("*"):
                        if file.is_file():
                            arcname = f"{dir_name}/{item_name}/{file.relative_to(item)}"
                            zf.write(file, arcname)
                elif item.is_file():
                    zf.write(item, f"{dir_name}/{item_name}")

        # Write manifest.yaml
        manifest_data = {
            "format_version": 1,
            "created_at": created_at,
            "vaults": manifest_entries,
        }
        zf.writestr("manifest.yaml", yaml.dump(manifest_data, default_flow_style=False))

        # Write config_snapshot.yaml
        snapshot = {
            "format_version": 1,
            "created_at": created_at,
            "default_vault_name": default_vault_name,
            "default_tool": config.get("default_tool"),
            "nav_mode": config.get("nav_mode"),
            "tools": config.get("tools", {}),
        }
        zf.writestr("config_snapshot.yaml", yaml.dump(snapshot, default_flow_style=False))

    return {"success": True, "output": str(out), "vault_count": len(vault_paths), "error": None}


def restore_catalog(archive_path: str) -> dict[str, Any]:
    """Restore vaults from a backup archive and apply config settings.

    Vaults are always extracted to ~/.config/artifactr/vaults/<vault-name>/.
    Name conflicts are resolved by appending -1, -2, etc.

    Args:
        archive_path: Path to the backup .zip archive.

    Returns:
        Result dict with keys:
            - success: bool
            - extracted: list[dict] with name, path for each vault
            - renames: dict mapping original name → assigned name
            - warnings: list[str]
            - errors: list[str]
            - error: str | None (fatal errors only)
    """
    from .config import get_config_dir

    arc = Path(archive_path)
    if not arc.exists() or not arc.is_file():
        return {"success": False, "extracted": [], "renames": {}, "warnings": [], "errors": [], "error": f"Archive not found: {archive_path}"}

    try:
        if not zipfile.is_zipfile(arc):
            return {"success": False, "extracted": [], "renames": {}, "warnings": [], "errors": [], "error": f"Not a valid zip archive: {archive_path}"}
    except OSError as e:
        return {"success": False, "extracted": [], "renames": {}, "warnings": [], "errors": [], "error": str(e)}

    with zipfile.ZipFile(arc, "r") as zf:
        names_in_zip = zf.namelist()
        if "manifest.yaml" not in names_in_zip:
            return {"success": False, "extracted": [], "renames": {}, "warnings": [], "errors": [], "error": "Archive does not contain manifest.yaml"}
        if "config_snapshot.yaml" not in names_in_zip:
            return {"success": False, "extracted": [], "renames": {}, "warnings": [], "errors": [], "error": "Archive does not contain config_snapshot.yaml"}

        manifest_data = yaml.safe_load(zf.read("manifest.yaml").decode("utf-8"))
        snapshot = yaml.safe_load(zf.read("config_snapshot.yaml").decode("utf-8"))

    if not manifest_data or "vaults" not in manifest_data:
        return {"success": False, "extracted": [], "renames": {}, "warnings": [], "errors": [], "error": "manifest.yaml is invalid or missing 'vaults' key"}

    dest_base = get_config_dir() / "vaults"
    dest_base.mkdir(parents=True, exist_ok=True)

    extracted: list[dict[str, Any]] = []
    renames: dict[str, str] = {}
    warnings: list[str] = []
    errors: list[str] = []

    config = load_config()
    existing_names = set(config["vault_names"].values())

    def _unique_name(name: str) -> str:
        candidate = name
        suffix = 1
        while candidate in existing_names:
            candidate = f"{name}-{suffix}"
            suffix += 1
        return candidate

    with zipfile.ZipFile(arc, "r") as zf:
        for entry in manifest_data["vaults"]:
            vault_name = entry.get("name")
            vault_dir_name = entry.get("dir", vault_name)

            assigned_name = _unique_name(vault_name)
            if assigned_name != vault_name:
                renames[vault_name] = assigned_name

            vault_dest = dest_base / assigned_name
            existing_names.add(assigned_name)

            # Extract vault files
            prefix = f"{vault_dir_name}/"
            for member in zf.infolist():
                if member.filename.startswith(prefix):
                    rel = member.filename[len(prefix):]
                    if not rel:
                        continue
                    target = vault_dest / rel
                    if member.filename.endswith("/"):
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(zf.read(member.filename))

            # Register vault
            reg = add_vaults([str(vault_dest)], name=assigned_name)
            if reg["errors"]:
                errors.extend(reg["errors"])
            else:
                extracted.append({"name": assigned_name, "path": str(vault_dest)})

    # Apply config settings from snapshot
    config = load_config()
    if snapshot:
        if "default_tool" in snapshot and snapshot["default_tool"] is not None:
            config["default_tool"] = snapshot["default_tool"]
        if "nav_mode" in snapshot:
            config["nav_mode"] = snapshot["nav_mode"]
        if "tools" in snapshot and snapshot["tools"]:
            config["tools"].update(snapshot["tools"])

        # Set default vault
        default_vault_name = snapshot.get("default_vault_name")
        if default_vault_name is not None:
            # Find the extracted vault (accounting for renames)
            target_name = renames.get(default_vault_name, default_vault_name)
            found_path = None
            for entry in extracted:
                if entry["name"] == target_name:
                    found_path = entry["path"]
                    break
            if found_path:
                config["default_vault"] = found_path
            else:
                warnings.append(
                    f"default_vault_name '{default_vault_name}' not found in archive; default vault unchanged."
                )

        save_config(config)

    return {
        "success": True,
        "extracted": extracted,
        "renames": renames,
        "warnings": warnings,
        "errors": errors,
        "error": None,
    }
