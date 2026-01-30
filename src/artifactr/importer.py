"""Import logic for Artifactr.

This module handles importing artifacts from vaults into target git repositories.
"""

import shutil
from pathlib import Path
from typing import Any

from .catalog import get_default_vault, get_vault_by_name_or_path
from .tools import ARTIFACT_TYPES, get_source, get_supported_tools, get_tool
from .utils import is_git_repo


ARTIFACTR_HEADER = "# Added by artifactr"


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


def copy_with_prompt(src: Path, dst: Path, link: bool = False) -> dict[str, int]:
    """Copy or symlink files/directories with user confirmation for overwrites.

    Args:
        src: Source path (file or directory).
        dst: Destination path.
        link: If True, create symlinks instead of copying.

    Returns:
        Dict with counts: {"copied": n, "skipped": n}
    """
    copied = 0
    skipped = 0

    if src.is_file():
        # Ensure parent directory exists
        dst.parent.mkdir(parents=True, exist_ok=True)

        if dst.exists() or dst.is_symlink():
            if prompt_overwrite(dst):
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

                result = copy_with_prompt(src_file, dst_file, link=link)
                copied += result["copied"]
                skipped += result["skipped"]

    return {"copied": copied, "skipped": skipped}


def import_artifacts(
    target: str,
    vault: str | None = None,
    tools: list[str] | None = None,
    link: bool = False,
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

    # Validate target is a git repository
    if not target_path.exists():
        errors.append(f"Error: Target path does not exist: {target}")
    elif not is_git_repo(target_path):
        errors.append("Error: Target is not a git repository!")

    # Resolve vault path
    if vault is None:
        vault_path_str = get_default_vault()
        if vault_path_str is None:
            errors.append("Error: No default vault set. Use 'art vault add' to add a vault.")
    else:
        vault_path_str = get_vault_by_name_or_path(vault)
        if vault_path_str is None:
            errors.append("Error: Specified vault does not exist.")

    # Determine which tools to use
    supported_tools = get_supported_tools()
    if tools is None:
        selected_tools = supported_tools
    else:
        selected_tools = []
        unsupported = []
        for tool_name in tools:
            if tool_name in supported_tools:
                selected_tools.append(tool_name)
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

    # Import artifacts for each tool
    for tool_name in selected_tools:
        tool_adapter = get_tool(tool_name)
        if tool_adapter is None:
            continue

        imported[tool_name] = {}

        for artifact_type in ARTIFACT_TYPES:
            source_path = get_source(artifact_type, vault_path)

            # Skip if source doesn't exist or is empty
            if not source_path.exists() or not any(source_path.iterdir()):
                imported[tool_name][artifact_type] = 0
                continue

            dest_path = tool_adapter.get_destination(artifact_type, target_path)

            # Copy or symlink each artifact in the source directory
            artifact_count = 0
            for item in source_path.iterdir():
                item_dest = dest_path / item.name
                result = copy_with_prompt(item, item_dest, link=link)
                artifact_count += result["copied"]
                total_skipped += result["skipped"]

                # Track pattern for git exclude (relative to repo root)
                rel_dest = item_dest.relative_to(target_path)
                exclude_patterns.append(str(rel_dest))

            imported[tool_name][artifact_type] = artifact_count

    # Add imported paths to .git/info/exclude
    if exclude_patterns:
        add_to_git_exclude(target_path, exclude_patterns)

    return {
        "success": True,
        "errors": [],
        "imported": imported,
        "skipped": total_skipped,
    }
