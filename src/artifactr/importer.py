"""Import logic for Artifactr.

This module handles importing artifacts from vaults into target git repositories.
"""

import fnmatch
import os
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Any

from .catalog import get_default_vault, get_vault_by_name_or_path, list_vaults
from .tools import get_source, get_supported_tools, get_tool, resolve_tool_name
from .utils import is_git_repo


ARTIFACTR_HEADER = "# Added by artifactr"


def _parse_cache_file(content: str) -> tuple[dict[str, str], set[str]]:
    """Parse a v2 cache file into vault_paths dict and imported entries set.

    Handles both legacy (no headers) and v2 (with section headers) formats.
    """
    vault_paths: dict[str, str] = {}
    imported: set[str] = set()
    current_section = "imported"  # Default for legacy files

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if line == "[vault_paths]":
            current_section = "vault_paths"
            continue
        if line == "[imported]":
            current_section = "imported"
            continue
        if current_section == "vault_paths":
            if "=" in line:
                label, path = line.split("=", 1)
                vault_paths[label.strip()] = path.strip()
        else:
            imported.add(line)

    return vault_paths, imported


def _write_cache_file(cache_file: Path, vault_paths: dict[str, str], entries: list[str] | set[str]) -> None:
    """Write a v2 format cache file with [vault_paths] and [imported] sections."""
    lines = []
    if vault_paths:
        lines.append("[vault_paths]")
        for label, path in sorted(vault_paths.items()):
            lines.append(f"{label}={path}")
        lines.append("")
    lines.append("[imported]")
    for entry in sorted(entries):
        lines.append(entry)
    lines.append("")
    cache_file.write_text("\n".join(lines), encoding="utf-8")


def update_cache_link_state(cache_file: Path, entry_base: str, new_state: str) -> None:
    """Update the link state suffix of a specific entry in a cache file.

    Args:
        cache_file: Path to the .art-cache/imported file.
        entry_base: The entry base name (e.g., "favorites.claude-code.helping-hand").
        new_state: New link state ("linked", "copied", or "win_hardlinked").
    """
    if not cache_file.is_file():
        return

    content = cache_file.read_text(encoding="utf-8")
    vault_paths, imported = _parse_cache_file(content)

    updated: set[str] = set()
    for entry in imported:
        base = entry.rsplit(":", 1)[0] if ":" in entry else entry
        if base == entry_base:
            updated.add(f"{base}:{new_state}")
        else:
            updated.add(entry)

    _write_cache_file(cache_file, vault_paths, updated)


def load_vault_paths_from_cache(cache_file: Path) -> dict[str, str]:
    """Read the [vault_paths] section from a cache file.

    Args:
        cache_file: Path to the .art-cache/imported file.

    Returns:
        Dict mapping vault labels to filesystem paths.
    """
    if not cache_file.is_file():
        return {}

    content = cache_file.read_text(encoding="utf-8")
    vault_paths, _ = _parse_cache_file(content)
    return vault_paths


def are_hardlinked(file_a: Path, file_b: Path) -> bool:
    """Check if two files are hard links to the same data using inode comparison.

    Args:
        file_a: First file path.
        file_b: Second file path.

    Returns:
        True if both files share the same st_dev and st_ino.
    """
    try:
        stat_a = os.stat(file_a)
        stat_b = os.stat(file_b)
        return stat_a.st_dev == stat_b.st_dev and stat_a.st_ino == stat_b.st_ino
    except OSError:
        return False


def files_differ(path_a: Path, path_b: Path) -> bool:
    """Compare file contents to detect differences.

    Args:
        path_a: First file path.
        path_b: Second file path.

    Returns:
        True if file contents differ, False if identical.
    """
    try:
        return path_a.read_bytes() != path_b.read_bytes()
    except OSError:
        return True


def backup_artifact(artifact_path: Path, artifact_type: str, artifact_name: str, cache_dir: Path) -> Path:
    """Back up an artifact to .art-cache/backups/YYYY-MM-DD/<type>/<name>/.

    Args:
        artifact_path: Path to the artifact to back up.
        artifact_type: Artifact type (e.g., "skills", "commands").
        artifact_name: Artifact name.
        cache_dir: Path to the .art-cache directory.

    Returns:
        Path to the backup location.
    """
    today = date.today().isoformat()
    backup_dir = cache_dir / "backups" / today / artifact_type / artifact_name
    backup_dir.mkdir(parents=True, exist_ok=True)

    if artifact_path.is_dir():
        dest = backup_dir
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(artifact_path, dest, dirs_exist_ok=True)
    else:
        shutil.copy2(artifact_path, backup_dir / artifact_path.name)

    return backup_dir


def create_link(src: Path, dst: Path) -> str:
    """Create a symlink from dst to src, with Windows hard link fallback.

    On non-Windows, always uses symlink. On Windows, attempts symlink first,
    then offers hard link fallback with user approval.

    Args:
        src: Source file (the vault file to link to).
        dst: Destination path (where the link will be created).

    Returns:
        "linked" for symlink, "win_hardlinked" for Windows hard link.
    """
    if sys.platform != "win32":
        dst.symlink_to(src.resolve())
        return "linked"

    # Windows: try symlink first
    try:
        dst.symlink_to(src.resolve())
        return "linked"
    except OSError:
        # Symlink failed — offer hard link fallback
        print(f"\nSymlink creation failed (requires Developer Mode or admin privileges).")
        print(f"Hard links share the same file data — edits to one affect the other.")
        print(f"Unlike symlinks, hard links require both files on the same volume.")
        try:
            response = input("Fall back to hard links? [y/N]: ")
        except EOFError:
            response = "n"

        if response.lower() not in ("y", "yes"):
            print("Tip: Enable Developer Mode: Settings > System > For Developers > Developer Mode > On")
            raise

        # Validate same volume
        try:
            src_stat = os.stat(src)
            dst_parent_stat = os.stat(dst.parent)
            if src_stat.st_dev != dst_parent_stat.st_dev:
                print(
                    "Error: Hard links require both paths on the same volume.\n"
                    "Tip: Enable Developer Mode for symlink support:\n"
                    "  Settings > System > For Developers > Developer Mode > On\n"
                    "Or import without --link as an alternative.",
                    file=sys.stderr,
                )
                raise OSError("Cross-volume hard link not possible")
        except OSError:
            raise

        os.link(src.resolve(), dst)
        return "win_hardlinked"


def resolve_artifact_patterns(patterns: list[str], cache_entries: list[dict]) -> list[dict]:
    """Resolve artifact name patterns against imported cache entries using fnmatch.

    Args:
        patterns: List of artifact names or glob patterns.
        cache_entries: List of cache entry dicts with at least "name" key.

    Returns:
        List of matching cache entry dicts (deduplicated).
    """
    matched: list[dict] = []
    seen: set[str] = set()

    for pattern in patterns:
        for entry in cache_entries:
            name = entry["name"]
            if name in seen:
                continue
            if fnmatch.fnmatch(name, pattern):
                matched.append(entry)
                seen.add(name)

    return matched


def _type_included(artifact_type: str, artifact_name: str | None, type_filters: dict | None) -> bool:
    """Check if an artifact type (and optionally name) passes type filters.

    Args:
        artifact_type: The plural artifact type (skills, commands, agents).
        artifact_name: The artifact name, or None for type-level check.
        type_filters: The type filter dict, or None for no filtering.

    Returns:
        True if the artifact should be included.
    """
    if type_filters is None:
        return True
    if artifact_type not in type_filters:
        return False
    filter_val = type_filters[artifact_type]
    if filter_val is True:
        return True
    if isinstance(filter_val, list) and artifact_name is not None:
        return artifact_name in filter_val
    return artifact_name is None  # type-level check passes if type is in filters


def add_to_git_exclude(repo_path: Path, patterns: list[str]) -> None:
    """Add patterns to the .git/info/exclude file.

    Args:
        repo_path: Path to the git repository.
        patterns: List of patterns to add to the exclude file.
    """
    exclude_file = repo_path / ".git" / "info" / "exclude"

    # Read existing patterns
    existing_patterns: set[str] = set()
    has_artifactr_header = False

    if exclude_file.exists():
        content = exclude_file.read_text()
        has_artifactr_header = ARTIFACTR_HEADER in content
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                existing_patterns.add(stripped)

    # Determine new patterns to add
    new_patterns = [p for p in patterns if p not in existing_patterns]

    if not new_patterns:
        return

    # Append new patterns to the file
    with exclude_file.open("a") as f:
        # Add header comment if this is the first artifactr entry
        if not has_artifactr_header:
            f.write(f"\n{ARTIFACTR_HEADER}\n")

        for pattern in new_patterns:
            f.write(f"{pattern}\n")


def prompt_overwrite(path: Path) -> bool:
    """Prompt the user whether to overwrite an existing file.

    Args:
        path: Path to the file that would be overwritten.

    Returns:
        True if user confirms overwrite, False otherwise.
    """
    try:
        response = input(f"File already exists: {path}\nOverwrite? [y/N]: ")
        return response.lower() in ("y", "yes")
    except EOFError:
        # Default to not overwriting if input stream is closed
        return False


def copy_with_prompt(
    src: Path, dst: Path, link: bool = False, force: bool = False
) -> dict[str, int]:
    """Copy or symlink files/directories with user confirmation for overwrites.

    Args:
        src: Source path (file or directory).
        dst: Destination path.
        link: If True, create symlinks instead of copying.
        force: If True, skip overwrite prompts and overwrite directly.

    Returns:
        Dict with counts: {"copied": n, "skipped": n}
    """
    copied = 0
    skipped = 0

    if src.is_file():
        # Ensure parent directory exists
        dst.parent.mkdir(parents=True, exist_ok=True)

        if dst.exists() or dst.is_symlink():
            if force or prompt_overwrite(dst):
                dst.unlink()
                if link:
                    create_link(src, dst)
                else:
                    shutil.copy2(src, dst)
                copied += 1
            else:
                skipped += 1
        else:
            if link:
                create_link(src, dst)
            else:
                shutil.copy2(src, dst)
            copied += 1

    elif src.is_dir():
        # Recursively handle each file in the directory
        for src_file in src.rglob("*"):
            if src_file.is_file():
                # Calculate relative path and destination
                rel_path = src_file.relative_to(src)
                dst_file = dst / rel_path

                result = copy_with_prompt(src_file, dst_file, link=link, force=force)
                copied += result["copied"]
                skipped += result["skipped"]

    return {"copied": copied, "skipped": skipped}


def update_import_cache(
    target: Path,
    vault_path: str,
    vault_name: str | None,
    tool_name: str,
    artifact_names: list[str],
    link_state: str = "copied",
) -> None:
    """Update the .art-cache/imported tracking file.

    Args:
        target: Path to the target directory.
        vault_path: The vault's filesystem path.
        vault_name: The vault's assigned name, or None.
        tool_name: The tool the artifacts were imported for.
        artifact_names: List of artifact names that were imported.
        link_state: Link state suffix ("linked", "copied", or "win_hardlinked").
    """
    vault_label = vault_name if vault_name else Path(vault_path).name

    cache_dir = target / ".art-cache"
    cache_dir.mkdir(exist_ok=True)

    cache_file = cache_dir / "imported"

    # Read existing content and parse sections
    vault_paths_section: dict[str, str] = {}
    imported_entries: set[str] = set()
    if cache_file.is_file():
        content = cache_file.read_text(encoding="utf-8")
        vault_paths_section, imported_entries = _parse_cache_file(content)

    # Update vault path
    vault_paths_section[vault_label] = vault_path

    # Build new entries (strip old suffix for duplicate check)
    existing_base_names = set()
    for entry in imported_entries:
        base = entry.rsplit(":", 1)[0] if ":" in entry else entry
        existing_base_names.add(base)

    new_entries = list(imported_entries)
    for name in artifact_names:
        base = f"{vault_label}.{tool_name}.{name}"
        if base not in existing_base_names:
            new_entries.append(f"{base}:{link_state}")

    # Write full file
    _write_cache_file(cache_file, vault_paths_section, new_entries)


def resolve_artifact_names(
    vault_path: Path, artifact_specs: list[str]
) -> list[dict]:
    """Resolve artifact specifiers to actual artifacts in a vault.

    Args:
        vault_path: Path to the vault directory.
        artifact_specs: List of artifact specifiers (e.g., ["helping-hand", "skills/write-thing"]).

    Returns:
        List of dicts with keys: name, type, source.
    """
    resolved = []

    for spec in artifact_specs:
        if "/" in spec:
            # Type-prefixed specifier
            type_prefix, name = spec.split("/", 1)
            matches = []
            if type_prefix == "skills" and (vault_path / "skills" / name).is_dir():
                matches.append({
                    "name": name,
                    "type": "skills",
                    "source": vault_path / "skills" / name,
                })
            elif type_prefix == "agents" and (vault_path / "agents" / f"{name}.md").is_file():
                matches.append({
                    "name": name,
                    "type": "agents",
                    "source": vault_path / "agents" / f"{name}.md",
                })
            elif type_prefix == "commands" and (vault_path / "commands" / f"{name}.md").is_file():
                matches.append({
                    "name": name,
                    "type": "commands",
                    "source": vault_path / "commands" / f"{name}.md",
                })

            if not matches:
                print(f"Error: Artifact not found: {spec}", file=sys.stderr)
                continue
            resolved.extend(matches)
        else:
            # Unqualified name — search all types
            matches = []
            if (vault_path / "skills" / spec).is_dir():
                matches.append({
                    "name": spec,
                    "type": "skills",
                    "source": vault_path / "skills" / spec,
                })
            if (vault_path / "agents" / f"{spec}.md").is_file():
                matches.append({
                    "name": spec,
                    "type": "agents",
                    "source": vault_path / "agents" / f"{spec}.md",
                })
            if (vault_path / "commands" / f"{spec}.md").is_file():
                matches.append({
                    "name": spec,
                    "type": "commands",
                    "source": vault_path / "commands" / f"{spec}.md",
                })

            if not matches:
                print(f"Error: Artifact not found: {spec}", file=sys.stderr)
                continue
            elif len(matches) == 1:
                resolved.append(matches[0])
            else:
                # Ambiguous — prompt user
                print(f'Ambiguous artifact name: "{spec}"')
                print("Found in multiple types:")
                for i, m in enumerate(matches, 1):
                    print(f"  {i}. {m['type']}/{m['name']}")
                try:
                    choice = input(f"Select one [1-{len(matches)}]: ")
                    idx = int(choice) - 1
                    if 0 <= idx < len(matches):
                        resolved.append(matches[idx])
                    else:
                        print(f"Invalid selection, skipping: {spec}", file=sys.stderr)
                except (EOFError, ValueError):
                    print(f"Skipping: {spec}", file=sys.stderr)

    return resolved


def remove_from_import_cache(
    target: Path,
    artifact_names: list[str],
) -> None:
    """Remove entries from .art-cache/imported for the given artifact names.

    Args:
        target: Path to the target directory.
        artifact_names: List of artifact names to remove from cache.
    """
    cache_file = target / ".art-cache" / "imported"
    if not cache_file.is_file():
        return

    names_set = set(artifact_names)
    content = cache_file.read_text(encoding="utf-8")
    vault_paths, imported = _parse_cache_file(content)

    remaining: set[str] = set()
    for entry in imported:
        # Strip suffix before parsing
        base = entry.rsplit(":", 1)[0] if ":" in entry else entry
        parts = base.split(".")
        if len(parts) >= 3:
            artifact_name = parts[-1]
            if artifact_name in names_set:
                continue
        remaining.add(entry)

    _write_cache_file(cache_file, vault_paths, remaining)


def remove_from_global_import_cache(
    artifact_names: list[str],
) -> None:
    """Remove entries from ~/.config/artifactr/.art-cache-global/imported.

    Args:
        artifact_names: List of artifact names to remove from global cache.
    """
    cache_file = Path.home() / ".config" / "artifactr" / ".art-cache-global" / "imported"
    if not cache_file.is_file():
        return

    names_set = set(artifact_names)
    content = cache_file.read_text(encoding="utf-8")
    vault_paths, imported = _parse_cache_file(content)

    remaining: set[str] = set()
    for entry in imported:
        base = entry.rsplit(":", 1)[0] if ":" in entry else entry
        parts = base.split(".")
        if len(parts) >= 3:
            artifact_name = parts[-1]
            if artifact_name in names_set:
                continue
        remaining.add(entry)

    _write_cache_file(cache_file, vault_paths, remaining)


def import_artifacts(
    target: str,
    vault: str | None = None,
    tools: list[str] | None = None,
    link: bool = False,
    artifacts: list[str] | None = None,
    force: bool = False,
    no_exclude: bool = False,
    type_filters: dict | None = None,
) -> dict[str, Any]:
    """Import artifacts from a vault into a target git repository.

    Args:
        target: Path to the target git repository.
        vault: Vault name or path to import from. Uses default vault if None.
        tools: List of tool names to import for. Imports for all tools if None.
        link: If True, create symlinks instead of copying files.

    Returns:
        Result dict with keys:
            - success: True if import succeeded, False if validation failed
            - errors: List of error messages
            - imported: Dict mapping tool names to artifact counts
            - skipped: Number of files user chose not to overwrite
    """
    errors: list[str] = []
    imported: dict[str, dict[str, int]] = {}
    total_skipped = 0
    exclude_patterns: list[str] = []

    # Resolve target path
    target_path = Path(target).resolve()

    # Validate target exists
    if not target_path.exists():
        errors.append(f"Error: Target path does not exist: {target}")

    # Resolve vault path
    if vault is None:
        vault_path_str = get_default_vault()
        if vault_path_str is None:
            errors.append("Error: No default vault set. Use 'art vault add' or 'art vault init' to set up a vault.")
    else:
        vault_path_str = get_vault_by_name_or_path(vault)
        if vault_path_str is None:
            errors.append("Error: Specified vault does not exist.")

    # Determine which tools to use (resolve aliases first)
    supported_tools = get_supported_tools()
    if tools is None:
        selected_tools = supported_tools
    else:
        selected_tools = []
        unsupported = []
        for tool_name in tools:
            resolved_name = resolve_tool_name(tool_name)
            if resolved_name in supported_tools:
                selected_tools.append(resolved_name)
            else:
                unsupported.append(tool_name)
        if unsupported:
            errors.append(f"Error: Tools specified are not supported: {', '.join(unsupported)}")

    # Return early if validation failed
    if errors:
        return {
            "success": False,
            "errors": errors,
            "imported": {},
            "skipped": 0,
        }

    # At this point, vault_path_str is guaranteed to be set
    vault_path = Path(vault_path_str)

    # Look up vault name for import cache
    vault_info = list_vaults()
    vault_display_name = vault_info["vault_names"].get(vault_path_str)

    # Resolve selective artifacts if specified
    resolved_artifacts = None
    if artifacts is not None:
        resolved_artifacts = resolve_artifact_names(vault_path, artifacts)
        if not resolved_artifacts:
            return {
                "success": True,
                "errors": [],
                "imported": {},
                "skipped": 0,
            }

    # Import artifacts for each tool
    for tool_name in selected_tools:
        tool_adapter = get_tool(tool_name)
        if tool_adapter is None:
            continue

        imported[tool_name] = {}
        imported_artifact_names: list[str] = []

        supported = tool_adapter.supported_types

        if resolved_artifacts is not None:
            # Selective import — only the resolved artifacts
            for artifact_type in supported:
                imported[tool_name][artifact_type] = 0

            for art in resolved_artifacts:
                artifact_type = art["type"]
                # Skip unsupported artifact types silently
                if artifact_type not in supported:
                    continue
                if not _type_included(artifact_type, art["name"], type_filters):
                    continue
                source = art["source"]
                dest_path = tool_adapter.get_destination(artifact_type, target_path)
                item_dest = dest_path / source.name
                result = copy_with_prompt(source, item_dest, link=link, force=force)
                imported[tool_name][artifact_type] = (
                    imported[tool_name].get(artifact_type, 0) + (1 if result["copied"] > 0 else 0)
                )
                total_skipped += result["skipped"]

                if result["copied"] > 0:
                    imported_artifact_names.append(art["name"])

                rel_dest = item_dest.relative_to(target_path)
                exclude_patterns.append(str(rel_dest))
        else:
            # Full import — only supported artifact types
            for artifact_type in supported:
                if not _type_included(artifact_type, None, type_filters):
                    imported[tool_name][artifact_type] = 0
                    continue

                source_path = get_source(artifact_type, vault_path)

                # Skip if source doesn't exist or is empty
                if not source_path.exists() or not any(source_path.iterdir()):
                    imported[tool_name][artifact_type] = 0
                    continue

                dest_path = tool_adapter.get_destination(artifact_type, target_path)

                # Copy or symlink each artifact in the source directory
                artifact_count = 0
                for item in source_path.iterdir():
                    art_name = item.stem if item.is_file() else item.name
                    if not _type_included(artifact_type, art_name, type_filters):
                        continue

                    item_dest = dest_path / item.name
                    result = copy_with_prompt(item, item_dest, link=link, force=force)
                    if result["copied"] > 0:
                        artifact_count += 1
                    total_skipped += result["skipped"]

                    # Track successfully imported artifact names
                    if result["copied"] > 0:
                        imported_artifact_names.append(art_name)

                    # Track pattern for git exclude (relative to repo root)
                    rel_dest = item_dest.relative_to(target_path)
                    exclude_patterns.append(str(rel_dest))

                imported[tool_name][artifact_type] = artifact_count

        # Update import cache for this tool
        if imported_artifact_names:
            update_import_cache(
                target_path, vault_path_str, vault_display_name,
                tool_name, imported_artifact_names,
                link_state="linked" if link else "copied",
            )

    # Add imported paths and .art-cache to .git/info/exclude (only for git repos)
    if is_git_repo(target_path):
        if no_exclude:
            add_to_git_exclude(target_path, [".art-cache"])
        else:
            exclude_patterns.append(".art-cache")
            add_to_git_exclude(target_path, exclude_patterns)

    return {
        "success": True,
        "errors": [],
        "imported": imported,
        "skipped": total_skipped,
    }


def prompt_create_directory(path: Path) -> bool:
    """Prompt the user to create a missing directory.

    Args:
        path: Directory path that does not exist.

    Returns:
        True if user confirms creation, False otherwise.
    """
    try:
        response = input(f"Directory does not exist: {path}\nCreate it? [y/N]: ")
        if response.lower() in ("y", "yes"):
            path.mkdir(parents=True, exist_ok=True)
            return True
        return False
    except EOFError:
        return False


def update_global_import_cache(
    vault_path: str,
    vault_name: str | None,
    tool_name: str,
    artifact_names: list[str],
    link_state: str = "copied",
) -> None:
    """Update the global import tracking file at ~/.config/artifactr/.art-cache-global/imported.

    Args:
        vault_path: The vault's filesystem path.
        vault_name: The vault's assigned name, or None.
        tool_name: The tool the artifacts were imported for.
        artifact_names: List of artifact names that were imported.
        link_state: Link state suffix ("linked", "copied", or "win_hardlinked").
    """
    vault_label = vault_name if vault_name else Path(vault_path).name

    cache_dir = Path.home() / ".config" / "artifactr" / ".art-cache-global"
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_file = cache_dir / "imported"

    # Read existing content and parse sections
    vault_paths_section: dict[str, str] = {}
    imported_entries: set[str] = set()
    if cache_file.is_file():
        content = cache_file.read_text(encoding="utf-8")
        vault_paths_section, imported_entries = _parse_cache_file(content)

    # Update vault path
    vault_paths_section[vault_label] = vault_path

    # Build new entries (strip old suffix for duplicate check)
    existing_base_names = set()
    for entry in imported_entries:
        base = entry.rsplit(":", 1)[0] if ":" in entry else entry
        existing_base_names.add(base)

    new_entries = list(imported_entries)
    for name in artifact_names:
        base = f"{vault_label}.{tool_name}.{name}"
        if base not in existing_base_names:
            new_entries.append(f"{base}:{link_state}")

    # Write full file
    _write_cache_file(cache_file, vault_paths_section, new_entries)


def import_artifacts_global(
    vault: str | None = None,
    tools: list[str] | None = None,
    link: bool = False,
    artifacts: list[str] | None = None,
    force: bool = False,
    type_filters: dict | None = None,
) -> dict[str, Any]:
    """Import artifacts from a vault into global config directories.

    Args:
        vault: Vault name or path to import from. Uses default vault if None.
        tools: List of tool names to import for. Imports for all tools if None.
        link: If True, create symlinks instead of copying files.
        artifacts: List of artifact specifiers to import selectively.
        force: If True, skip overwrite prompts.

    Returns:
        Result dict with keys:
            - success: True if import succeeded, False if validation failed
            - errors: List of error messages
            - imported: Dict mapping tool names to artifact counts
            - skipped: Number of files user chose not to overwrite
    """
    errors: list[str] = []
    imported: dict[str, dict[str, int]] = {}
    total_skipped = 0

    # Resolve vault path
    vault_path_str: str | None
    if vault is None:
        vault_path_str = get_default_vault()
        if vault_path_str is None:
            errors.append("Error: No default vault set. Use 'art vault add' or 'art vault init' to set up a vault.")
    else:
        vault_path_str = get_vault_by_name_or_path(vault)
        if vault_path_str is None:
            errors.append("Error: Specified vault does not exist.")

    # Determine which tools to use (resolve aliases first)
    supported_tools = get_supported_tools()
    if tools is None:
        selected_tools = supported_tools
    else:
        selected_tools = []
        unsupported = []
        for tool_name in tools:
            resolved_name = resolve_tool_name(tool_name)
            if resolved_name in supported_tools:
                selected_tools.append(resolved_name)
            else:
                unsupported.append(tool_name)
        if unsupported:
            errors.append(f"Error: Tools specified are not supported: {', '.join(unsupported)}")

    # Return early if validation failed
    if errors:
        return {
            "success": False,
            "errors": errors,
            "imported": {},
            "skipped": 0,
        }

    # At this point, vault_path_str is guaranteed to be set
    vault_path = Path(vault_path_str)

    # Look up vault name for import cache
    vault_info = list_vaults()
    vault_display_name = vault_info["vault_names"].get(vault_path_str)

    # Resolve selective artifacts if specified
    resolved_artifacts = None
    if artifacts is not None:
        resolved_artifacts = resolve_artifact_names(vault_path, artifacts)
        if not resolved_artifacts:
            return {
                "success": True,
                "errors": [],
                "imported": {},
                "skipped": 0,
            }

    # Import artifacts for each tool
    for tool_name in selected_tools:
        tool_adapter = get_tool(tool_name)
        if tool_adapter is None:
            continue

        imported[tool_name] = {}
        imported_artifact_names: list[str] = []

        supported = tool_adapter.supported_types

        if resolved_artifacts is not None:
            # Selective import — only the resolved artifacts
            for artifact_type in supported:
                imported[tool_name][artifact_type] = 0

            for art in resolved_artifacts:
                artifact_type = art["type"]
                # Skip unsupported artifact types silently
                if artifact_type not in supported:
                    continue
                if not _type_included(artifact_type, art["name"], type_filters):
                    continue
                source = art["source"]
                dest_path = tool_adapter.get_global_destination(artifact_type)

                # Prompt to create directory if it doesn't exist
                if not dest_path.exists():
                    if not prompt_create_directory(dest_path):
                        continue

                item_dest = dest_path / source.name
                result = copy_with_prompt(source, item_dest, link=link, force=force)
                imported[tool_name][artifact_type] = (
                    imported[tool_name].get(artifact_type, 0) + (1 if result["copied"] > 0 else 0)
                )
                total_skipped += result["skipped"]

                if result["copied"] > 0:
                    imported_artifact_names.append(art["name"])
        else:
            # Full import — only supported artifact types
            for artifact_type in supported:
                if not _type_included(artifact_type, None, type_filters):
                    imported[tool_name][artifact_type] = 0
                    continue

                source_path = get_source(artifact_type, vault_path)

                # Skip if source doesn't exist or is empty
                if not source_path.exists() or not any(source_path.iterdir()):
                    imported[tool_name][artifact_type] = 0
                    continue

                dest_path = tool_adapter.get_global_destination(artifact_type)

                # Prompt to create directory if it doesn't exist
                if not dest_path.exists():
                    if not prompt_create_directory(dest_path):
                        imported[tool_name][artifact_type] = 0
                        continue

                # Copy or symlink each artifact in the source directory
                artifact_count = 0
                for item in source_path.iterdir():
                    art_name = item.stem if item.is_file() else item.name
                    if not _type_included(artifact_type, art_name, type_filters):
                        continue

                    item_dest = dest_path / item.name
                    result = copy_with_prompt(item, item_dest, link=link, force=force)
                    if result["copied"] > 0:
                        artifact_count += 1
                    total_skipped += result["skipped"]

                    # Track successfully imported artifact names
                    if result["copied"] > 0:
                        imported_artifact_names.append(art_name)

                imported[tool_name][artifact_type] = artifact_count

        # Update global import cache for this tool
        if imported_artifact_names:
            update_global_import_cache(
                vault_path_str, vault_display_name,
                tool_name, imported_artifact_names,
                link_state="linked" if link else "copied",
            )

    return {
        "success": True,
        "errors": [],
        "imported": imported,
        "skipped": total_skipped,
    }


def _load_cache_entries_for_linking(cache_file: Path) -> list[dict]:
    """Load cache entries with link state info for link/unlink operations.

    Returns list of dicts with keys: name, vault_label, tool, link_state, entry_base.
    """
    if not cache_file.is_file():
        return []

    content = cache_file.read_text(encoding="utf-8")
    _, imported = _parse_cache_file(content)

    entries = []
    for raw in imported:
        # Parse suffix
        if ":" in raw:
            base, link_state = raw.rsplit(":", 1)
        else:
            base = raw
            link_state = "copied"

        parts = base.split(".")
        if len(parts) < 3:
            continue

        vault_label = parts[0]
        tool = parts[1]
        name = parts[-1]

        entries.append({
            "name": name,
            "vault_label": vault_label,
            "tool": tool,
            "link_state": link_state,
            "entry_base": base,
        })

    return entries


def _resolve_vault_source(
    artifact_name: str,
    artifact_tool: str,
    vault_path: Path,
) -> Path | None:
    """Resolve the vault source path for a given artifact.

    Searches skills/, commands/, agents/ in the vault.
    """
    skill_dir = vault_path / "skills" / artifact_name
    if skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file():
        return skill_dir

    cmd_file = vault_path / "commands" / f"{artifact_name}.md"
    if cmd_file.is_file():
        return cmd_file

    agent_file = vault_path / "agents" / f"{artifact_name}.md"
    if agent_file.is_file():
        return agent_file

    return None


def _resolve_artifact_dest(
    artifact_name: str,
    tool_name: str,
    target: Path,
) -> tuple[Path | None, str]:
    """Resolve the destination path and type for an artifact in a project.

    Returns (path, artifact_type) or (None, "unknown").
    """
    tool_adapter = get_tool(tool_name)
    if tool_adapter is None:
        return None, "unknown"

    for artifact_type in tool_adapter.supported_types:
        dest_path = tool_adapter.get_destination(artifact_type, target)
        if artifact_type == "skills":
            candidate = dest_path / artifact_name
            if candidate.is_dir() and (candidate / "SKILL.md").is_file():
                return candidate, artifact_type
        else:
            candidate = dest_path / f"{artifact_name}.md"
            if candidate.is_file() or candidate.is_symlink():
                return candidate, artifact_type

    return None, "unknown"


def _resolve_artifact_dest_global(
    artifact_name: str,
    tool_name: str,
) -> tuple[Path | None, str]:
    """Resolve the destination path and type for a global artifact.

    Returns (path, artifact_type) or (None, "unknown").
    """
    tool_adapter = get_tool(tool_name)
    if tool_adapter is None:
        return None, "unknown"

    for artifact_type in tool_adapter.supported_types:
        dest_path = tool_adapter.get_global_destination(artifact_type)
        if artifact_type == "skills":
            candidate = dest_path / artifact_name
            if candidate.is_dir() and (candidate / "SKILL.md").is_file():
                return candidate, artifact_type
        else:
            candidate = dest_path / f"{artifact_name}.md"
            if candidate.is_file() or candidate.is_symlink():
                return candidate, artifact_type

    return None, "unknown"


def _prompt_diff_action(artifact_name: str) -> str:
    """Prompt user for action when local copy differs from vault.

    Returns "backup", "skip", or "link".
    """
    try:
        response = input(
            f"  '{artifact_name}' has local changes. "
            f"[b]ackup and link / [s]kip / [l]ink anyway: "
        )
    except EOFError:
        return "skip"

    response = response.strip().lower()
    if response in ("b", "backup"):
        return "backup"
    if response in ("l", "link"):
        return "link"
    return "skip"


def _link_single_file(
    src: Path,
    dst: Path,
    artifact_name: str,
    artifact_type: str,
    cache_dir: Path,
    force: bool,
) -> tuple[str, str]:
    """Link a single file: detect diff, prompt/backup, replace with symlink.

    Returns (action, link_state) where action is "linked", "skipped", etc.
    """
    if dst.is_symlink():
        return "skipped_already_linked", "linked"

    if are_hardlinked(dst, src):
        return "skipped_already_linked", "win_hardlinked"

    if files_differ(dst, src):
        if force:
            backup_artifact(dst, artifact_type, artifact_name, cache_dir)
            action_taken = "backed_up_and_linked"
        else:
            choice = _prompt_diff_action(artifact_name)
            if choice == "backup":
                backup_artifact(dst, artifact_type, artifact_name, cache_dir)
                action_taken = "backed_up_and_linked"
            elif choice == "link":
                action_taken = "linked"
            else:
                return "skipped", "copied"
    else:
        action_taken = "linked"

    dst.unlink()
    link_state = create_link(src, dst)
    return action_taken, link_state


def _link_single_artifact(
    src: Path,
    dst: Path,
    artifact_name: str,
    artifact_type: str,
    cache_dir: Path,
    force: bool,
) -> tuple[str, str]:
    """Link a single artifact (file or directory).

    For directories (skills), links each file inside.
    Returns (action, link_state).
    """
    if src.is_file() and (dst.is_file() or dst.is_symlink()):
        return _link_single_file(src, dst, artifact_name, artifact_type, cache_dir, force)
    elif src.is_dir() and dst.is_dir():
        any_linked = False
        link_state = "linked"
        for src_file in src.rglob("*"):
            if not src_file.is_file():
                continue
            rel = src_file.relative_to(src)
            dst_file = dst / rel
            if not dst_file.exists() and not dst_file.is_symlink():
                continue
            action, ls = _link_single_file(src_file, dst_file, artifact_name, artifact_type, cache_dir, force)
            if action not in ("skipped", "skipped_already_linked"):
                any_linked = True
                link_state = ls
        if any_linked:
            return "linked", link_state
        return "skipped_already_linked", link_state
    return "skipped", "copied"


def link_artifacts(
    target: Path,
    names: list[str],
    all_flag: bool,
    force: bool,
    vault_labels: list[str],
    type_filters: dict | None,
) -> dict:
    """Link copied artifacts to their vault sources in a project.

    Args:
        vault_labels: Vault labels to scope the operation to.
    """
    cache_file = target / ".art-cache" / "imported"
    cache_dir = target / ".art-cache"
    entries = _load_cache_entries_for_linking(cache_file)

    # Filter entries to only those from the specified vaults
    entries = [e for e in entries if e["vault_label"] in vault_labels]

    if not entries:
        return {"linked": 0, "skipped": 0, "backed_up": 0, "errors": ["No imported artifacts found for the specified vault(s)."]}

    if all_flag:
        selected = entries
    elif names:
        selected = resolve_artifact_patterns(names, entries)
        if not selected:
            return {"linked": 0, "skipped": 0, "backed_up": 0, "errors": ["No artifacts matched the given pattern(s)."]}
    else:
        return {"linked": 0, "skipped": 0, "backed_up": 0,
                "errors": ["Specify artifact names or use --all/-a to link all artifacts."]}

    vault_paths = load_vault_paths_from_cache(cache_file)

    linked = 0
    skipped = 0
    backed_up = 0
    errors: list[str] = []

    for entry in selected:
        name = entry["name"]
        vault_label = entry["vault_label"]
        tool = entry["tool"]
        link_state = entry["link_state"]

        dst, artifact_type = _resolve_artifact_dest(name, tool, target)
        if dst is None:
            errors.append(f"Could not find artifact '{name}' in project.")
            continue

        if type_filters and artifact_type not in type_filters:
            continue

        if link_state in ("linked", "win_hardlinked"):
            print(f"  '{name}' is already linked, skipping.")
            skipped += 1
            continue

        vault_path_str = vault_paths.get(vault_label)
        if vault_path_str is None:
            vault_path_str = get_vault_by_name_or_path(vault_label)

        if vault_path_str is None:
            errors.append(f"Could not resolve vault '{vault_label}' for artifact '{name}'.")
            continue

        vault_path = Path(vault_path_str)
        src = _resolve_vault_source(name, tool, vault_path)
        if src is None:
            errors.append(f"Vault source not found for artifact '{name}'.")
            continue

        action, new_state = _link_single_artifact(src, dst, name, artifact_type, cache_dir, force)

        if action == "skipped_already_linked":
            print(f"  '{name}' is already linked, skipping.")
            skipped += 1
        elif action == "skipped":
            skipped += 1
        else:
            if "backed_up" in action:
                backed_up += 1
                print(f"  '{name}' backed up and linked.")
            else:
                print(f"  '{name}' linked.")
            linked += 1
            update_cache_link_state(cache_file, entry["entry_base"], new_state)

    return {"linked": linked, "skipped": skipped, "backed_up": backed_up, "errors": errors}


def unlink_artifacts(
    target: Path,
    names: list[str],
    all_flag: bool,
    vault_labels: list[str],
    type_filters: dict | None,
) -> dict:
    """Unlink symlinked artifacts to independent copies in a project.

    Args:
        vault_labels: Vault labels to scope the operation to.
    """
    cache_file = target / ".art-cache" / "imported"
    entries = _load_cache_entries_for_linking(cache_file)

    # Filter entries to only those from the specified vaults
    entries = [e for e in entries if e["vault_label"] in vault_labels]

    if not entries:
        return {"unlinked": 0, "skipped": 0, "errors": ["No imported artifacts found for the specified vault(s)."]}

    if all_flag:
        selected = entries
    elif names:
        selected = resolve_artifact_patterns(names, entries)
        if not selected:
            return {"unlinked": 0, "skipped": 0, "errors": ["No artifacts matched the given pattern(s)."]}
    else:
        return {"unlinked": 0, "skipped": 0,
                "errors": ["Specify artifact names or use --all/-a to unlink all artifacts."]}

    unlinked = 0
    skipped_count = 0
    errors: list[str] = []

    for entry in selected:
        name = entry["name"]
        tool = entry["tool"]
        link_state = entry["link_state"]

        dst, artifact_type = _resolve_artifact_dest(name, tool, target)
        if dst is None:
            errors.append(f"Could not find artifact '{name}' in project.")
            continue

        if type_filters and artifact_type not in type_filters:
            continue

        if link_state == "copied":
            print(f"  '{name}' is already a copy, skipping.")
            skipped_count += 1
            continue

        if dst.is_file() or dst.is_symlink():
            content = dst.read_bytes()
            dst.unlink()
            dst.write_bytes(content)
            print(f"  '{name}' unlinked.")
            unlinked += 1
        elif dst.is_dir():
            for f in list(dst.rglob("*")):
                if f.is_file() or f.is_symlink():
                    file_content = f.read_bytes()
                    f.unlink()
                    f.write_bytes(file_content)
            print(f"  '{name}' unlinked.")
            unlinked += 1
        else:
            skipped_count += 1
            continue

        update_cache_link_state(cache_file, entry["entry_base"], "copied")

    return {"unlinked": unlinked, "skipped": skipped_count, "errors": errors}


def link_artifacts_global(
    names: list[str],
    all_flag: bool,
    force: bool,
    vault_labels: list[str],
    type_filters: dict | None,
) -> dict:
    """Link copied global artifacts to their vault sources.

    Args:
        vault_labels: Vault labels to scope the operation to.
    """
    cache_dir = Path.home() / ".config" / "artifactr" / ".art-cache-global"
    cache_file = cache_dir / "imported"
    entries = _load_cache_entries_for_linking(cache_file)

    # Filter entries to only those from the specified vaults
    entries = [e for e in entries if e["vault_label"] in vault_labels]

    if not entries:
        return {"linked": 0, "skipped": 0, "backed_up": 0, "errors": ["No globally imported artifacts found for the specified vault(s)."]}

    if all_flag:
        selected = entries
    elif names:
        selected = resolve_artifact_patterns(names, entries)
        if not selected:
            return {"linked": 0, "skipped": 0, "backed_up": 0, "errors": ["No artifacts matched the given pattern(s)."]}
    else:
        return {"linked": 0, "skipped": 0, "backed_up": 0,
                "errors": ["Specify artifact names or use --all/-a to link all artifacts."]}

    vault_paths = load_vault_paths_from_cache(cache_file)

    linked = 0
    skipped_count = 0
    backed_up = 0
    errors: list[str] = []

    for entry in selected:
        name = entry["name"]
        vault_label = entry["vault_label"]
        tool = entry["tool"]
        link_state = entry["link_state"]

        dst, artifact_type = _resolve_artifact_dest_global(name, tool)
        if dst is None:
            errors.append(f"Could not find artifact '{name}' in global config.")
            continue

        if type_filters and artifact_type not in type_filters:
            continue

        if link_state in ("linked", "win_hardlinked"):
            print(f"  '{name}' is already linked, skipping.")
            skipped_count += 1
            continue

        vault_path_str = vault_paths.get(vault_label)
        if vault_path_str is None:
            vault_path_str = get_vault_by_name_or_path(vault_label)

        if vault_path_str is None:
            errors.append(f"Could not resolve vault '{vault_label}' for artifact '{name}'.")
            continue

        vault_path = Path(vault_path_str)
        src = _resolve_vault_source(name, tool, vault_path)
        if src is None:
            errors.append(f"Vault source not found for artifact '{name}'.")
            continue

        action, new_state = _link_single_artifact(src, dst, name, artifact_type, cache_dir, force)

        if action == "skipped_already_linked":
            print(f"  '{name}' is already linked, skipping.")
            skipped_count += 1
        elif action == "skipped":
            skipped_count += 1
        else:
            if "backed_up" in action:
                backed_up += 1
                print(f"  '{name}' backed up and linked.")
            else:
                print(f"  '{name}' linked.")
            linked += 1
            update_cache_link_state(cache_file, entry["entry_base"], new_state)

    return {"linked": linked, "skipped": skipped_count, "backed_up": backed_up, "errors": errors}


def unlink_artifacts_global(
    names: list[str],
    all_flag: bool,
    vault_labels: list[str],
    type_filters: dict | None,
) -> dict:
    """Unlink symlinked global artifacts to independent copies.

    Args:
        vault_labels: Vault labels to scope the operation to.
    """
    cache_dir = Path.home() / ".config" / "artifactr" / ".art-cache-global"
    cache_file = cache_dir / "imported"
    entries = _load_cache_entries_for_linking(cache_file)

    # Filter entries to only those from the specified vaults
    entries = [e for e in entries if e["vault_label"] in vault_labels]

    if not entries:
        return {"unlinked": 0, "skipped": 0, "errors": ["No globally imported artifacts found for the specified vault(s)."]}

    if all_flag:
        selected = entries
    elif names:
        selected = resolve_artifact_patterns(names, entries)
        if not selected:
            return {"unlinked": 0, "skipped": 0, "errors": ["No artifacts matched the given pattern(s)."]}
    else:
        return {"unlinked": 0, "skipped": 0,
                "errors": ["Specify artifact names or use --all/-a to unlink all artifacts."]}

    unlinked = 0
    skipped_count = 0
    errors: list[str] = []

    for entry in selected:
        name = entry["name"]
        tool = entry["tool"]
        link_state = entry["link_state"]

        dst, artifact_type = _resolve_artifact_dest_global(name, tool)
        if dst is None:
            errors.append(f"Could not find artifact '{name}' in global config.")
            continue

        if type_filters and artifact_type not in type_filters:
            continue

        if link_state == "copied":
            print(f"  '{name}' is already a copy, skipping.")
            skipped_count += 1
            continue

        if dst.is_file() or dst.is_symlink():
            content = dst.read_bytes()
            dst.unlink()
            dst.write_bytes(content)
            print(f"  '{name}' unlinked.")
            unlinked += 1
        elif dst.is_dir():
            for f in list(dst.rglob("*")):
                if f.is_file() or f.is_symlink():
                    file_content = f.read_bytes()
                    f.unlink()
                    f.write_bytes(file_content)
            print(f"  '{name}' unlinked.")
            unlinked += 1
        else:
            skipped_count += 1
            continue

        update_cache_link_state(cache_file, entry["entry_base"], "copied")

    return {"unlinked": unlinked, "skipped": skipped_count, "errors": errors}
