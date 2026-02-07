"""Tool adapters for different AI coding assistants."""

from .base import ARTIFACT_TYPES, ToolAdapter, get_source
from .claude_code import ClaudeCodeAdapter
from .opencode import OpenCodeAdapter

# Registry of all supported tools
TOOL_REGISTRY: dict[str, ToolAdapter] = {
    "claude-code": ClaudeCodeAdapter(),
    "opencode": OpenCodeAdapter(),
}


def get_tool(name: str) -> ToolAdapter | None:
    """Get a tool adapter by name."""
    return TOOL_REGISTRY.get(name)


def get_supported_tools() -> list[str]:
    """Return list of all supported tool names."""
    return list(TOOL_REGISTRY.keys())


def get_tool_config_dirs() -> dict[str, str]:
    """Return a mapping of tool name to config directory name."""
    return {name: adapter.config_dir for name, adapter in TOOL_REGISTRY.items()}


__all__ = [
    "ARTIFACT_TYPES",
    "ToolAdapter",
    "get_source",
    "get_tool",
    "get_supported_tools",
    "get_tool_config_dirs",
]
