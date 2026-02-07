"""Artifact discovery logic for Artifactr.

This module provides shared discovery functions used by both
the spelunk and store commands.
"""

from pathlib import Path

import yaml

from .tools import get_tool_config_dirs


def discover_artifacts(target: Path) -> list[dict]:
    """Discover artifacts in a target directory.

    Searches tool config directories for skills, agents, and commands.

    Args:
        target: Path to the directory to probe.

    Returns:
        List of artifact dicts sorted by tool, type, then name.
    """
    artifacts = []
    tool_config_dirs = get_tool_config_dirs()

    for tool_name, config_dir in tool_config_dirs.items():
        config_path = target / config_dir
        if not config_path.is_dir():
            continue

        # Check skills/ — subdirectories containing SKILL.md
        skills_path = config_path / "skills"
        if skills_path.is_dir():
            for item in skills_path.iterdir():
                if item.is_dir() and (item / "SKILL.md").is_file():
                    artifacts.append({
                        "name": item.name,
                        "type": "skill",
                        "type_plural": "skills",
                        "path": item.resolve(),
                        "tool": tool_name,
                        "config_dir": config_dir,
                    })

        # Check agents/ — .md files directly inside
        agents_path = config_path / "agents"
        if agents_path.is_dir():
            for item in agents_path.iterdir():
                if item.is_file() and item.suffix == ".md":
                    artifacts.append({
                        "name": item.stem,
                        "type": "agent",
                        "type_plural": "agents",
                        "path": item.resolve(),
                        "tool": tool_name,
                        "config_dir": config_dir,
                    })

        # Check commands/ — .md files directly inside
        commands_path = config_path / "commands"
        if commands_path.is_dir():
            for item in commands_path.iterdir():
                if item.is_file() and item.suffix == ".md":
                    artifacts.append({
                        "name": item.stem,
                        "type": "command",
                        "type_plural": "commands",
                        "path": item.resolve(),
                        "tool": tool_name,
                        "config_dir": config_dir,
                    })

    artifacts.sort(key=lambda a: (a["tool"], a["type"], a["name"]))
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
    to lists of vault names they were imported from.

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

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = line.split(".")
        if len(parts) < 3:
            continue

        vault_name = parts[0]
        artifact_name = parts[-1]

        if artifact_name not in result:
            result[artifact_name] = []
        if vault_name not in result[artifact_name]:
            result[artifact_name].append(vault_name)

    return result
