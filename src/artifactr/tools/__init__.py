"""Tool adapters for different AI coding assistants."""

from .base import ARTIFACT_TYPES, GenericToolAdapter, get_source

# Built-in tool definitions as data
BUILTIN_TOOLS: dict[str, dict] = {
    "claude-code": {
        "aliases": ["claude"],
        "skills": ".claude/skills",
        "commands": ".claude/commands",
        "agents": ".claude/agents",
        "global_skills": "$HOME/.claude/skills",
        "global_commands": "$HOME/.claude/commands",
        "global_agents": "$HOME/.claude/agents",
    },
    "opencode": {
        "skills": ".opencode/skills",
        "commands": ".opencode/commands",
        "agents": ".opencode/agents",
        "global_skills": "$HOME/.config/opencode/skills",
        "global_commands": "$HOME/.config/opencode/commands",
        "global_agents": "$HOME/.config/opencode/agents",
    },
    "codex": {
        "skills": ".agents/skills",
        "global_skills": "$HOME/.agents/skills",
    },
}


def _build_tool_registry(
    extra_tools: dict[str, dict] | None = None,
    vault_tools: dict[str, dict] | None = None,
) -> dict[str, GenericToolAdapter]:
    """Build the tool registry from built-in defaults + config sources.

    Precedence (ascending): BUILTIN_TOOLS < extra_tools (global config) < vault_tools.
    Higher tiers fully replace lower tiers for the same tool name.
    """
    merged: dict[str, dict] = {}
    merged.update(BUILTIN_TOOLS)
    if extra_tools:
        merged.update(extra_tools)
    if vault_tools:
        merged.update(vault_tools)

    registry: dict[str, GenericToolAdapter] = {}
    for name, config in merged.items():
        registry[name] = GenericToolAdapter(name, config)
    return registry


# Module-level registry built from built-ins only.
# Use get_tool() with vault_tools for vault-scoped resolution.
_REGISTRY: dict[str, GenericToolAdapter] = _build_tool_registry()


def _get_merged_definitions(
    extra_tools: dict[str, dict] | None = None,
    vault_tools: dict[str, dict] | None = None,
) -> dict[str, dict]:
    """Merge tool definitions from all tiers and return the raw dicts."""
    merged: dict[str, dict] = {}
    merged.update(BUILTIN_TOOLS)
    if extra_tools:
        merged.update(extra_tools)
    if vault_tools:
        merged.update(vault_tools)
    return merged


def reload_registry(
    global_tools: dict[str, dict] | None = None,
    vault_tools: dict[str, dict] | None = None,
) -> None:
    """Rebuild the module-level registry with additional tool definitions."""
    global _REGISTRY
    _REGISTRY = _build_tool_registry(extra_tools=global_tools, vault_tools=vault_tools)


def resolve_tool_name(
    name: str,
    extra_tools: dict[str, dict] | None = None,
    vault_tools: dict[str, dict] | None = None,
) -> str:
    """Resolve a tool alias to its canonical name.

    Scans aliases fields from all loaded tool definitions.
    Returns the canonical name if an alias is found, otherwise returns
    the name unchanged (passthrough for canonical and unknown names).
    """
    merged = _get_merged_definitions(extra_tools=extra_tools, vault_tools=vault_tools)
    for tool_name, config in merged.items():
        aliases = config.get("aliases", [])
        if name in aliases:
            return tool_name
    return name


def get_tool(
    name: str,
    global_tools: dict[str, dict] | None = None,
    vault_tools: dict[str, dict] | None = None,
) -> GenericToolAdapter | None:
    """Get a tool adapter by name. Resolves aliases before lookup."""
    resolved = resolve_tool_name(name, extra_tools=global_tools, vault_tools=vault_tools)
    if global_tools or vault_tools:
        registry = _build_tool_registry(extra_tools=global_tools, vault_tools=vault_tools)
        return registry.get(resolved)
    return _REGISTRY.get(resolved)


def get_aliases_for_tool(
    canonical_name: str,
    extra_tools: dict[str, dict] | None = None,
    vault_tools: dict[str, dict] | None = None,
) -> list[str]:
    """Return all aliases that map to the given canonical tool name."""
    merged = _get_merged_definitions(extra_tools=extra_tools, vault_tools=vault_tools)
    config = merged.get(canonical_name, {})
    return config.get("aliases", [])


def get_supported_tools(
    global_tools: dict[str, dict] | None = None,
    vault_tools: dict[str, dict] | None = None,
) -> list[str]:
    """Return list of all supported tool names."""
    if global_tools or vault_tools:
        registry = _build_tool_registry(extra_tools=global_tools, vault_tools=vault_tools)
        return list(registry.keys())
    return list(_REGISTRY.keys())


def get_tool_config_dirs(
    global_tools: dict[str, dict] | None = None,
    vault_tools: dict[str, dict] | None = None,
) -> dict[str, dict[str, str]]:
    """Return a mapping of tool name to dict of artifact_type -> repo-local path.

    Only includes artifact types the tool supports.
    """
    if global_tools or vault_tools:
        registry = _build_tool_registry(extra_tools=global_tools, vault_tools=vault_tools)
    else:
        registry = _REGISTRY

    result: dict[str, dict[str, str]] = {}
    for name, adapter in registry.items():
        paths: dict[str, str] = {}
        for art_type in adapter.supported_types:
            # Get the raw (unexpanded) repo-local path from config
            paths[art_type] = adapter._config.get(art_type, "")
        result[name] = paths
    return result


def get_tool_global_dirs(
    global_tools: dict[str, dict] | None = None,
    vault_tools: dict[str, dict] | None = None,
) -> dict[str, dict[str, str]]:
    """Return a mapping of tool name to dict of artifact_type -> global path.

    Only includes artifact types the tool has global paths for.
    """
    if global_tools or vault_tools:
        registry = _build_tool_registry(extra_tools=global_tools, vault_tools=vault_tools)
    else:
        registry = _REGISTRY

    result: dict[str, dict[str, str]] = {}
    for name, adapter in registry.items():
        paths: dict[str, str] = {}
        for art_type in adapter.supported_types:
            global_key = f"global_{art_type}"
            if global_key in adapter._config:
                paths[art_type] = adapter._expanded.get(global_key, "")
        if paths:
            result[name] = paths
    return result


def get_tool_source(
    tool_name: str,
    global_tools: dict[str, dict] | None = None,
    vault_tools: dict[str, dict] | None = None,
    vault_name: str | None = None,
) -> str:
    """Determine the source tier for a tool definition.

    Returns one of: 'built-in', 'user global config', 'vault (<name>)'.
    """
    if vault_tools and tool_name in vault_tools:
        label = vault_name or "unknown"
        return f"vault ({label})"
    if global_tools and tool_name in global_tools:
        return "user global config"
    if tool_name in BUILTIN_TOOLS:
        return "built-in"
    return "unknown"


__all__ = [
    "ARTIFACT_TYPES",
    "BUILTIN_TOOLS",
    "GenericToolAdapter",
    "get_source",
    "get_tool",
    "get_aliases_for_tool",
    "get_supported_tools",
    "get_tool_config_dirs",
    "get_tool_global_dirs",
    "get_tool_source",
    "reload_registry",
    "resolve_tool_name",
]
