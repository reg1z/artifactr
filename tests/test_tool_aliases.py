"""Tests for tool alias support."""

import pytest

from artifactr.tools import (
    BUILTIN_TOOLS,
    get_aliases_for_tool,
    get_tool,
    resolve_tool_name,
)


class TestResolveToolName:
    """Tests for resolve_tool_name function."""

    def test_resolves_known_alias(self):
        """Verify known alias resolves to canonical name."""
        assert resolve_tool_name("claude") == "claude-code"

    def test_passthrough_canonical_name(self):
        """Verify canonical name passes through unchanged."""
        assert resolve_tool_name("claude-code") == "claude-code"

    def test_passthrough_unknown_name(self):
        """Verify unknown name passes through unchanged."""
        assert resolve_tool_name("unknown-tool") == "unknown-tool"


class TestGetToolWithAlias:
    """Tests for alias-aware get_tool function."""

    def test_lookup_by_alias(self):
        """Verify get_tool works with alias."""
        adapter = get_tool("claude")
        assert adapter is not None
        assert adapter.name == "claude-code"

    def test_lookup_by_canonical_name(self):
        """Verify get_tool still works with canonical name."""
        adapter = get_tool("claude-code")
        assert adapter is not None
        assert adapter.name == "claude-code"

    def test_lookup_unknown_returns_none(self):
        """Verify unknown name returns None."""
        assert get_tool("nonexistent") is None


class TestGetAliasesForTool:
    """Tests for get_aliases_for_tool function."""

    def test_aliases_for_claude_code(self):
        """Verify claude-code has the claude alias."""
        aliases = get_aliases_for_tool("claude-code")
        assert "claude" in aliases

    def test_no_aliases_for_opencode(self):
        """Verify opencode has no aliases."""
        aliases = get_aliases_for_tool("opencode")
        assert aliases == []

    def test_no_aliases_for_unknown(self):
        """Verify unknown tool has no aliases."""
        aliases = get_aliases_for_tool("nonexistent")
        assert aliases == []


class TestBuiltinToolAliases:
    """Tests for aliases defined in BUILTIN_TOOLS."""

    def test_claude_alias_in_builtin(self):
        """Verify claude alias is defined in built-in tools."""
        assert "claude" in BUILTIN_TOOLS["claude-code"]["aliases"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
