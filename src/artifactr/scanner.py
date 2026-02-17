"""Artifact discovery logic for Artifactr.

This module provides shared discovery functions used by both
the spelunk and store commands.
"""

from pathlib import Path

import yaml

from .tools import get_tool_config_dirs, get_tool_global_dirs


def is_vault(directory: Path) -> bool:
    """Check if a directory is a vault by looking for vault.yaml."""
    return (directory / "vault.yaml").is_file()


def discover_artifacts(target: Path) -> list[dict]:
    """Discover artifacts in a target directory.

    Searches tool config directories for skills, agents, and commands,
    respecting each tool's supported artifact types.

    Args:
        target: Path to the directory to probe.

    Returns:
        List of artifact dicts sorted by tool, type, then name.
    """
    artifacts = []
    tool_config_dirs = get_tool_config_dirs()

    for tool_name, type_paths in tool_config_dirs.items():
        for artifact_type, repo_path in type_paths.items():
            base_path = target / repo_path

            if not base_path.is_dir():
                continue

            if artifact_type == "skills":
                for item in base_path.iterdir():
                    if item.is_dir() and (item / "SKILL.md").is_file():
                        artifacts.append({
                            "name": item.name,
                            "type": "skill",
                            "type_plural": "skills",
                            "path": item.resolve(),
                            "tool": tool_name,
                            "config_dir": repo_path,
                        })

            elif artifact_type == "agents":
                for item in base_path.iterdir():
                    if item.is_file() and item.suffix == ".md":
                        artifacts.append({
                            "name": item.stem,
                            "type": "agent",
                            "type_plural": "agents",
                            "path": item.resolve(),
                            "tool": tool_name,
                            "config_dir": repo_path,
                        })

            elif artifact_type == "commands":
                for item in base_path.iterdir():
                    if item.is_file() and item.suffix == ".md":
                        artifacts.append({
                            "name": item.stem,
                            "type": "command",
                            "type_plural": "commands",
                            "path": item.resolve(),
                            "tool": tool_name,
                            "config_dir": repo_path,
                        })

    artifacts.sort(key=lambda a: (a["tool"], a["type"], a["name"]))
    return artifacts


def discover_vault_artifacts(vault_path: Path) -> list[dict]:
    """Discover artifacts in a vault by scanning skills/, commands/, agents/ directly.

    Args:
        vault_path: Path to the vault directory.

    Returns:
        List of artifact dicts sorted by type then name.
    """
    artifacts = []

    for artifact_type, singular in [("skills", "skill"), ("commands", "command"), ("agents", "agent")]:
        base_path = vault_path / artifact_type
        if not base_path.is_dir():
            continue

        if artifact_type == "skills":
            for item in base_path.iterdir():
                if item.is_dir() and (item / "SKILL.md").is_file():
                    artifacts.append({
                        "name": item.name,
                        "type": singular,
                        "type_plural": artifact_type,
                        "path": item.resolve(),
                        "tool": "vault",
                        "config_dir": artifact_type,
                    })
        else:
            for item in base_path.iterdir():
                if item.is_file() and item.suffix == ".md":
                    artifacts.append({
                        "name": item.stem,
                        "type": singular,
                        "type_plural": artifact_type,
                        "path": item.resolve(),
                        "tool": "vault",
                        "config_dir": artifact_type,
                    })

    artifacts.sort(key=lambda a: (a["type"], a["name"]))
    return artifacts


def discover_global_artifacts(tools_filter: list[str] | None = None) -> list[dict]:
    """Discover artifacts in global config directories.

    Args:
        tools_filter: Optional list of tool names to filter to.

    Returns:
        List of artifact dicts sorted by tool, type, then name.
    """
    artifacts = []
    tool_global_dirs = get_tool_global_dirs()

    for tool_name, type_paths in tool_global_dirs.items():
        if tools_filter and tool_name not in tools_filter:
            continue

        for artifact_type, global_path in type_paths.items():
            base_path = Path(global_path)
            if not base_path.is_dir():
                continue

            if artifact_type == "skills":
                for item in base_path.iterdir():
                    if item.is_dir() and (item / "SKILL.md").is_file():
                        artifacts.append({
                            "name": item.name,
                            "type": "skill",
                            "type_plural": "skills",
                            "path": item.resolve(),
                            "tool": tool_name,
                            "config_dir": global_path,
                        })
            elif artifact_type == "agents":
                for item in base_path.iterdir():
                    if item.is_file() and item.suffix == ".md":
                        artifacts.append({
                            "name": item.stem,
                            "type": "agent",
                            "type_plural": "agents",
                            "path": item.resolve(),
                            "tool": tool_name,
                            "config_dir": global_path,
                        })
            elif artifact_type == "commands":
                for item in base_path.iterdir():
                    if item.is_file() and item.suffix == ".md":
                        artifacts.append({
                            "name": item.stem,
                            "type": "command",
                            "type_plural": "commands",
                            "path": item.resolve(),
                            "tool": tool_name,
                            "config_dir": global_path,
                        })

    artifacts.sort(key=lambda a: (a["tool"], a["type"], a["name"]))
    return artifacts


def discover_artifacts_by_structure(target_path: Path, depth: int = 2) -> list[dict]:
    """Walk directories up to `depth` levels looking for artifact-shaped content.

    Searches for directories named skills/, agents/, commands/ and identifies
    artifact-shaped content within them.

    Args:
        target_path: Root directory to scan from.
        depth: Maximum depth to recurse (0 = target only).

    Returns:
        List of artifact dicts sorted by type then name.
    """
    artifacts = []
    _artifact_dirs = {"skills", "agents", "commands"}

    def _scan_artifact_dir(base: Path, parent_label: str) -> None:
        for artifact_type, singular in [("skills", "skill"), ("commands", "command"), ("agents", "agent")]:
            art_dir = base / artifact_type
            if not art_dir.is_dir():
                continue
            if artifact_type == "skills":
                for item in art_dir.iterdir():
                    if item.is_dir() and (item / "SKILL.md").is_file():
                        artifacts.append({
                            "name": item.name,
                            "type": singular,
                            "type_plural": artifact_type,
                            "path": item.resolve(),
                            "tool": "directory",
                            "config_dir": str(base),
                        })
            else:
                for item in art_dir.iterdir():
                    if item.is_file() and item.suffix == ".md":
                        artifacts.append({
                            "name": item.stem,
                            "type": singular,
                            "type_plural": artifact_type,
                            "path": item.resolve(),
                            "tool": "directory",
                            "config_dir": str(base),
                        })

    def _walk(directory: Path, current_depth: int) -> None:
        # Check if this directory itself contains artifact dirs
        _scan_artifact_dir(directory, str(directory))
        if current_depth >= depth:
            return
        try:
            for child in sorted(directory.iterdir()):
                if child.is_dir() and child.name not in _artifact_dirs:
                    _walk(child, current_depth + 1)
        except PermissionError:
            pass

    _walk(target_path, 0)
    artifacts.sort(key=lambda a: (a["type"], a["name"]))
    return artifacts


def extract_description(artifact: dict) -> str:
    """Extract the description from an artifact's frontmatter.

    Args:
        artifact: Artifact dict from discover_artifacts().

    Returns:
        The description string, truncated to 50 chars if needed, or "-".
    """
    if artifact["type"] == "skill":
        file_path = artifact["path"] / "SKILL.md"
    else:
        file_path = artifact["path"]

    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "-"

    # Parse YAML frontmatter
    if not content.startswith("---"):
        return "-"

    # Find the closing ---
    end_index = content.find("---", 3)
    if end_index == -1:
        return "-"

    frontmatter_str = content[3:end_index].strip()
    if not frontmatter_str:
        return "-"

    try:
        frontmatter = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError:
        return "-"

    if not isinstance(frontmatter, dict):
        return "-"

    description = frontmatter.get("description", "")
    if not description:
        return "-"

    description = str(description)
    if len(description) > 50:
        return description[:50] + "..."

    return description


def load_import_cache(target: Path) -> dict[str, list[str]]:
    """Load the import cache from a target directory.

    Reads .art-cache/imported and returns a mapping of artifact names
    to lists of vault names they were imported from. Supports both
    legacy format (no headers, no suffixes) and v2 format (with
    [vault_paths]/[imported] sections and :linked/:copied/:win_hardlinked suffixes).

    Args:
        target: Path to the target directory.

    Returns:
        Dict mapping artifact names to vault name lists.
    """
    cache_file = target / ".art-cache" / "imported"
    if not cache_file.is_file():
        return {}

    result: dict[str, list[str]] = {}

    try:
        content = cache_file.read_text(encoding="utf-8")
    except OSError:
        return {}

    current_section = "imported"  # Default for legacy files

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        # Handle section headers
        if line == "[vault_paths]":
            current_section = "vault_paths"
            continue
        if line == "[imported]":
            current_section = "imported"
            continue

        # Skip vault_paths entries
        if current_section == "vault_paths":
            continue

        # Strip :suffix if present
        entry = line
        if ":" in entry:
            entry = entry.rsplit(":", 1)[0]

        parts = entry.split(".")
        if len(parts) < 3:
            continue

        vault_name = parts[0]
        artifact_name = parts[-1]

        if artifact_name not in result:
            result[artifact_name] = []
        if vault_name not in result[artifact_name]:
            result[artifact_name].append(vault_name)

    return result
