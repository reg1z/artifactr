"""Import logic for Artifactr.

This module handles importing artifacts from vaults into target git repositories.
"""

import shutil
import sys
from pathlib import Path
from typing import Any

from .catalog import get_default_vault, get_vault_by_name_or_path, list_vaults
from .tools import get_source, get_supported_tools, get_tool, resolve_tool_name
from .utils import is_git_repo


ARTIFACTR_HEADER = "# Added by artifactr"


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
                    dst.symlink_to(src.resolve())
                else:
                    shutil.copy2(src, dst)
                copied += 1
            else:
                skipped += 1
        else:
            if link:
                dst.symlink_to(src.resolve())
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
) -> None:
    """Update the .art-cache/imported tracking file.

    Args:
        target: Path to the target directory.
        vault_path: The vault's filesystem path.
        vault_name: The vault's assigned name, or None.
        tool_name: The tool the artifacts were imported for.
        artifact_names: List of artifact names that were imported.
    """
    vault_label = vault_name if vault_name else Path(vault_path).name

    cache_dir = target / ".art-cache"
    cache_dir.mkdir(exist_ok=True)

    cache_file = cache_dir / "imported"

    # Read existing lines to check for duplicates
    existing_lines: set[str] = set()
    if cache_file.is_file():
        existing_lines = set(cache_file.read_text(encoding="utf-8").splitlines())

    new_lines = []
    for name in artifact_names:
        line = f"{vault_label}.{tool_name}.{name}"
        if line not in existing_lines:
            new_lines.append(line)

    if new_lines:
        with cache_file.open("a", encoding="utf-8") as f:
            for line in new_lines:
                f.write(f"{line}\n")


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
    lines = cache_file.read_text(encoding="utf-8").splitlines()
    remaining = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(".")
        if len(parts) >= 3:
            artifact_name = parts[-1]
            if artifact_name in names_set:
                continue
        remaining.append(stripped)

    cache_file.write_text("\n".join(remaining) + ("\n" if remaining else ""), encoding="utf-8")


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
    lines = cache_file.read_text(encoding="utf-8").splitlines()
    remaining = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(".")
        if len(parts) >= 3:
            artifact_name = parts[-1]
            if artifact_name in names_set:
                continue
        remaining.append(stripped)

    cache_file.write_text("\n".join(remaining) + ("\n" if remaining else ""), encoding="utf-8")


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
) -> None:
    """Update the global import tracking file at ~/.config/artifactr/.art-cache-global/imported.

    Args:
        vault_path: The vault's filesystem path.
        vault_name: The vault's assigned name, or None.
        tool_name: The tool the artifacts were imported for.
        artifact_names: List of artifact names that were imported.
    """
    vault_label = vault_name if vault_name else Path(vault_path).name

    cache_dir = Path.home() / ".config" / "artifactr" / ".art-cache-global"
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_file = cache_dir / "imported"

    # Read existing lines to check for duplicates
    existing_lines: set[str] = set()
    if cache_file.is_file():
        existing_lines = set(cache_file.read_text(encoding="utf-8").splitlines())

    new_lines = []
    for name in artifact_names:
        line = f"{vault_label}.{tool_name}.{name}"
        if line not in existing_lines:
            new_lines.append(line)

    if new_lines:
        with cache_file.open("a", encoding="utf-8") as f:
            for line in new_lines:
                f.write(f"{line}\n")


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
            )

    return {
        "success": True,
        "errors": [],
        "imported": imported,
        "skipped": total_skipped,
    }
