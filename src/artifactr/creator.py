from pathlib import Path
from typing import Any

import yaml

from .catalog import get_default_tool, get_default_vault, get_vault_by_name_or_path
from .tools import get_tool, get_supported_tools

# Directory-based artifact types (create a directory with a main file inside)
_DIRECTORY_TYPES = {"skill"}
# File-based artifact types (create a single .md file)
_FILE_TYPES = {"command", "agent"}

# Mapping of artifact type to subdirectory name in vaults
_TYPE_SUBDIRS = {
    "skill": "skills",
    "command": "commands",
    "agent": "agents",
}


def create_artifact(
    artifact_type: str,
    name: str,
    description: str | None = None,
    content: str | None = None,
    extra_fields: dict[str, str] | None = None,
    target_path: Path | None = None,
) -> dict[str, Any]:
    """Create a new artifact with YAML frontmatter.

    Skills are directory-based (creates <target>/SKILL.md).
    Commands and agents are file-based (creates <target>.md or uses target_path directly).

    For commands, no 'name' field is added to frontmatter (filename IS the name).
    For agents and skills, 'name' is added to frontmatter.

    Args:
        artifact_type: One of "skill", "command", "agent".
        name: The artifact identifier.
        description: Description for frontmatter.
        content: Markdown body content after frontmatter.
        extra_fields: Additional key-value pairs for frontmatter.
        target_path: Full path to the artifact target.
            - For skills: the skill directory (e.g., vault/skills/my-skill/)
            - For commands/agents: the .md file path (e.g., vault/commands/my-cmd.md)

    Returns:
        Result dict with keys:
            - success: Whether the artifact was created
            - path: Path to the created file (if successful)
            - error: Error message (if failed)
    """
    if target_path is None:
        return {"success": False, "path": None, "error": "No target path provided"}

    if artifact_type in _DIRECTORY_TYPES:
        # Directory-based (skills)
        artifact_dir = target_path
        artifact_file = artifact_dir / "SKILL.md"

        if artifact_dir.exists():
            return {
                "success": False,
                "path": None,
                "error": f"Skill '{artifact_dir.name}' already exists at {artifact_dir}",
            }

        # Build frontmatter — skills include name
        frontmatter: dict[str, Any] = {"name": name}
        if description:
            frontmatter["description"] = description
        if extra_fields:
            frontmatter.update(extra_fields)

        yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        file_content = f"---\n{yaml_str}---\n"
        if content:
            file_content += content + "\n"

        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text(file_content)

        return {"success": True, "path": str(artifact_file), "error": None}
    else:
        # File-based (commands, agents)
        artifact_file = target_path

        if artifact_file.exists():
            return {
                "success": False,
                "path": None,
                "error": f"{artifact_type.title()} '{artifact_file.stem}' already exists at {artifact_file}",
            }

        # Build frontmatter
        frontmatter = {}
        # Agents include name in frontmatter; commands do not
        if artifact_type == "agent":
            frontmatter["name"] = name
        if description:
            frontmatter["description"] = description
        if extra_fields:
            frontmatter.update(extra_fields)

        yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        file_content = f"---\n{yaml_str}---\n"
        if content:
            file_content += content + "\n"

        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text(file_content)

        return {"success": True, "path": str(artifact_file), "error": None}


# Backward-compatible alias
def create_skill(
    name: str,
    description: str | None = None,
    content: str | None = None,
    extra_fields: dict[str, str] | None = None,
    target_path: Path | None = None,
) -> dict[str, Any]:
    """Create a new skill. Delegates to create_artifact."""
    return create_artifact(
        artifact_type="skill",
        name=name,
        description=description,
        content=content,
        extra_fields=extra_fields,
        target_path=target_path,
    )


def resolve_vault_target(
    artifact_name: str,
    artifact_type: str = "skill",
    vault: str | None = None,
) -> dict[str, Any]:
    """Resolve the target path for vault-based artifact creation.

    Args:
        artifact_name: The artifact identifier.
        artifact_type: One of "skill", "command", "agent".
        vault: Optional vault name or path. Uses default vault if None.

    Returns:
        Result dict with keys:
            - success: Whether resolution succeeded
            - path: The resolved target path (if successful)
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
                "error": "No default vault set. Use 'art vault add' or 'art vault init' to set up a vault.",
            }

    subdir = _TYPE_SUBDIRS[artifact_type]
    if artifact_type in _DIRECTORY_TYPES:
        target = Path(vault_path) / subdir / artifact_name
    else:
        target = Path(vault_path) / subdir / f"{artifact_name}.md"

    return {"success": True, "path": target, "error": None}


def resolve_project_target(
    artifact_name: str,
    artifact_type: str = "skill",
    tools: list[str] | None = None,
) -> dict[str, Any]:
    """Resolve target paths for project-local artifact creation.

    Args:
        artifact_name: The artifact identifier.
        artifact_type: One of "skill", "command", "agent".
        tools: List of tool names. Uses all supported tools if None.

    Returns:
        Result dict with keys:
            - success: Whether resolution succeeded
            - paths: List of resolved target paths (if successful)
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

    subdir = _TYPE_SUBDIRS[artifact_type]
    paths = []
    for tool_name in tools:
        adapter = get_tool(tool_name)
        if adapter is None:
            return {
                "success": False,
                "paths": [],
                "error": f"Unknown tool: {tool_name}",
            }
        if artifact_type in _DIRECTORY_TYPES:
            target = Path.cwd() / adapter.config_dir / subdir / artifact_name
        else:
            target = Path.cwd() / adapter.config_dir / subdir / f"{artifact_name}.md"
        paths.append(target)

    return {"success": True, "paths": paths, "error": None}


def resolve_edit_target(
    artifact_type: str,
    artifact_name: str,
    vault: str | None = None,
    here: bool = False,
    tools: list[str] | None = None,
) -> dict[str, Any]:
    """Resolve the path to an artifact's main file for editing.

    Args:
        artifact_type: One of "skill", "command", "agent".
        artifact_name: The artifact identifier.
        vault: Optional vault name or path (vault mode).
        here: If True, resolve in current project instead of vault.
        tools: Tool names for --here mode.

    Returns:
        Result dict with keys:
            - success: Whether resolution succeeded
            - path: The resolved file path (if successful)
            - error: Error message (if failed)
    """
    subdir = _TYPE_SUBDIRS.get(artifact_type)
    if subdir is None:
        return {"success": False, "path": None, "error": f"Invalid artifact type: {artifact_type}"}

    if here:
        # Project-local mode
        if tools is None:
            default_tool = get_default_tool()
            tools = [default_tool]

        for tool_name in tools:
            adapter = get_tool(tool_name)
            if adapter is None:
                return {"success": False, "path": None, "error": f"Unknown tool: {tool_name}"}

            if artifact_type in _DIRECTORY_TYPES:
                target = Path.cwd() / adapter.config_dir / subdir / artifact_name / "SKILL.md"
            else:
                target = Path.cwd() / adapter.config_dir / subdir / f"{artifact_name}.md"

            if target.exists():
                return {"success": True, "path": target, "error": None}

        return {
            "success": False,
            "path": None,
            "error": f"{artifact_type.title()} '{artifact_name}' not found in project",
        }
    else:
        # Vault mode
        if vault:
            vault_path = get_vault_by_name_or_path(vault)
            if vault_path is None:
                return {"success": False, "path": None, "error": f"Vault not found: {vault}"}
        else:
            vault_path = get_default_vault()
            if vault_path is None:
                return {
                    "success": False,
                    "path": None,
                    "error": "No default vault set. Use 'art vault add' or 'art vault init' to set up a vault.",
                }

        if artifact_type in _DIRECTORY_TYPES:
            target = Path(vault_path) / subdir / artifact_name / "SKILL.md"
        else:
            target = Path(vault_path) / subdir / f"{artifact_name}.md"

        if not target.exists():
            return {
                "success": False,
                "path": None,
                "error": f"{artifact_type.title()} '{artifact_name}' not found in vault",
            }

        return {"success": True, "path": target, "error": None}
