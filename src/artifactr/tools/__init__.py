"""Tool adapters for different AI coding assistants."""

from .base import ARTIFACT_TYPES, ToolAdapter, get_source
from .claude_code import ClaudeCodeAdapter
from .opencode import OpenCodeAdapter

# Registry of all supported tools
TOOL_REGISTRY: dict[str, ToolAdapter] = {
    "claude-code": ClaudeCodeAdapter(),
    "opencode": OpenCodeAdapter(),
}

# Alias mapping: alias -> canonical name
TOOL_ALIASES: dict[str, str] = {
    "claude": "claude-code",
}


def resolve_tool_name(name: str) -> str:
    """Resolve a tool alias to its canonical name.

    Returns the canonical name if an alias is found, otherwise returns
    the name unchanged (passthrough for canonical and unknown names).
    """
    return TOOL_ALIASES.get(name, name)


def get_tool(name: str) -> ToolAdapter | None:
    """Get a tool adapter by name. Resolves aliases before lookup."""
    return TOOL_REGISTRY.get(resolve_tool_name(name))


def get_aliases_for_tool(canonical_name: str) -> list[str]:
    """Return all aliases that map to the given canonical tool name."""
    return [alias for alias, target in TOOL_ALIASES.items() if target == canonical_name]


def get_supported_tools() -> list[str]:
    """Return list of all supported tool names."""
    return list(TOOL_REGISTRY.keys())


def get_tool_config_dirs() -> dict[str, str]:
    """Return a mapping of tool name to config directory name."""
    return {name: adapter.config_dir for name, adapter in TOOL_REGISTRY.items()}


__all__ = [
    "ARTIFACT_TYPES",
    "TOOL_ALIASES",
    "ToolAdapter",
    "get_source",
    "get_tool",
    "get_aliases_for_tool",
    "get_supported_tools",
    "get_tool_config_dirs",
    "resolve_tool_name",
]
