from pathlib import Path
from typing import Any

import yaml

from .catalog import get_default_vault, get_vault_by_name_or_path
from .tools import get_tool, get_supported_tools


def create_skill(
    name: str,
    description: str | None = None,
    content: str | None = None,
    extra_fields: dict[str, str] | None = None,
    target_path: Path | None = None,
) -> dict[str, Any]:
    """Create a new skill with a SKILL.md file containing YAML frontmatter.

    Args:
        name: The display name for the frontmatter (and directory name if target_path not given).
        description: Skill description for frontmatter.
        content: Markdown body content after frontmatter.
        extra_fields: Additional key-value pairs for frontmatter.
        target_path: Full path to the skill directory (e.g., vault/skills/my-skill/).

    Returns:
        Result dict with keys:
            - success: Whether the skill was created
            - path: Path to the created SKILL.md (if successful)
            - error: Error message (if failed)
    """
    if target_path is None:
        return {"success": False, "path": None, "error": "No target path provided"}

    skill_dir = target_path
    skill_file = skill_dir / "SKILL.md"

    # Overwrite protection
    if skill_dir.exists():
        return {
            "success": False,
            "path": None,
            "error": f"Skill '{skill_dir.name}' already exists at {skill_dir}",
        }

    # Build frontmatter
    frontmatter = {"name": name}
    if description:
        frontmatter["description"] = description
    if extra_fields:
        frontmatter.update(extra_fields)

    # Generate YAML frontmatter
    yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    file_content = f"---\n{yaml_str}---\n"
    if content:
        file_content += content + "\n"

    # Create directory and write file
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file.write_text(file_content)

    return {"success": True, "path": str(skill_file), "error": None}


def resolve_vault_target(skill_name: str, vault: str | None = None) -> dict[str, Any]:
    """Resolve the target path for vault-based skill creation.

    Args:
        skill_name: The skill identifier (directory name).
        vault: Optional vault name or path. Uses default vault if None.

    Returns:
        Result dict with keys:
            - success: Whether resolution succeeded
            - path: The resolved skill directory path (if successful)
            - error: Error message (if failed)
    """
    if vault:
        vault_path = get_vault_by_name_or_path(vault)
        if vault_path is None:
            return {
                "success": False,
                "path": None,
                "error": f"Vault not found: {vault}",
            }
    else:
        vault_path = get_default_vault()
        if vault_path is None:
            return {
                "success": False,
                "path": None,
                "error": "No default vault set. Add a vault with 'art vault add' first.",
            }

    target = Path(vault_path) / "skills" / skill_name
    return {"success": True, "path": target, "error": None}


def resolve_project_target(
    skill_name: str,
    tools: list[str] | None = None,
) -> dict[str, Any]:
    """Resolve target paths for project-local skill creation.

    Args:
        skill_name: The skill identifier (directory name).
        tools: List of tool names. Uses all supported tools if None.

    Returns:
        Result dict with keys:
            - success: Whether resolution succeeded
            - paths: List of resolved skill directory paths (if successful)
            - error: Error message (if failed)
    """
    if tools is None:
        supported = get_supported_tools()
        if not supported:
            return {
                "success": False,
                "paths": [],
                "error": "No supported tools found",
            }
        tools = supported

    paths = []
    for tool_name in tools:
        adapter = get_tool(tool_name)
        if adapter is None:
            return {
                "success": False,
                "paths": [],
                "error": f"Unknown tool: {tool_name}",
            }
        target = Path.cwd() / adapter.config_dir / "skills" / skill_name
        paths.append(target)

    return {"success": True, "paths": paths, "error": None}
