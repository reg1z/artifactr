"""Tests for the extensible tool system."""

import os
from pathlib import Path
from unittest import mock

import pytest
import yaml

from artifactr.tools import (
    BUILTIN_TOOLS,
    GenericToolAdapter,
    get_aliases_for_tool,
    get_supported_tools,
    get_tool,
    get_tool_config_dirs,
    get_tool_source,
    resolve_tool_name,
)
from artifactr.config import load_vault_metadata, save_vault_metadata


class TestGenericToolAdapter:
    """Tests for GenericToolAdapter."""

    def test_construction_full(self):
        """Verify adapter with all artifact types."""
        config = {
            "skills": ".test/skills",
            "commands": ".test/commands",
            "agents": ".test/agents",
            "global_skills": "/home/user/.test/skills",
            "global_commands": "/home/user/.test/commands",
            "global_agents": "/home/user/.test/agents",
        }
        adapter = GenericToolAdapter("test-tool", config)
        assert adapter.name == "test-tool"
        assert set(adapter.supported_types) == {"skills", "commands", "agents"}

    def test_construction_partial(self):
        """Verify adapter with skills only (like codex)."""
        config = {"skills": ".agents/skills", "global_skills": "/home/user/.agents/skills"}
        adapter = GenericToolAdapter("codex-like", config)
        assert adapter.supported_types == ["skills"]

    def test_get_destination_supported(self):
        """Verify destination for supported type."""
        config = {"skills": ".test/skills"}
        adapter = GenericToolAdapter("t", config)
        dest = adapter.get_destination("skills", Path("/repo"))
        assert dest == Path("/repo/.test/skills")

    def test_get_destination_unsupported(self):
        """Verify ValueError for unsupported type."""
        config = {"skills": ".test/skills"}
        adapter = GenericToolAdapter("t", config)
        with pytest.raises(ValueError, match="does not support"):
            adapter.get_destination("commands", Path("/repo"))

    def test_get_global_destination_supported(self):
        """Verify global destination for supported type."""
        config = {"skills": ".test/skills", "global_skills": "/home/user/.test/skills"}
        adapter = GenericToolAdapter("t", config)
        dest = adapter.get_global_destination("skills")
        assert dest == Path("/home/user/.test/skills")

    def test_get_global_destination_unsupported(self):
        """Verify ValueError for unsupported type global destination."""
        config = {"skills": ".test/skills"}
        adapter = GenericToolAdapter("t", config)
        with pytest.raises(ValueError, match="does not support"):
            adapter.get_global_destination("commands")

    def test_home_expansion(self):
        """Verify $HOME expansion in paths."""
        home = os.environ.get("HOME", str(Path.home()))
        config = {"skills": ".test/skills", "global_skills": "$HOME/.test/skills"}
        adapter = GenericToolAdapter("t", config)
        dest = adapter.get_global_destination("skills")
        assert str(dest).startswith(home)

    def test_tilde_expansion(self):
        """Verify ~ expansion in paths."""
        home = str(Path.home())
        config = {"skills": ".test/skills", "global_skills": "~/.test/skills"}
        adapter = GenericToolAdapter("t", config)
        dest = adapter.get_global_destination("skills")
        assert str(dest).startswith(home)

    def test_aliases_property(self):
        """Verify aliases from config."""
        config = {"skills": ".t/skills", "aliases": ["t", "tt"]}
        adapter = GenericToolAdapter("test", config)
        assert adapter.aliases == ["t", "tt"]

    def test_no_aliases(self):
        """Verify empty aliases when none defined."""
        config = {"skills": ".t/skills"}
        adapter = GenericToolAdapter("test", config)
        assert adapter.aliases == []


class TestBuiltinTools:
    """Tests for BUILTIN_TOOLS dict."""

    def test_claude_code_defined(self):
        assert "claude-code" in BUILTIN_TOOLS
        config = BUILTIN_TOOLS["claude-code"]
        assert config["skills"] == ".claude/skills"
        assert config["commands"] == ".claude/commands"
        assert config["agents"] == ".claude/agents"
        assert "claude" in config["aliases"]

    def test_opencode_defined(self):
        assert "opencode" in BUILTIN_TOOLS
        config = BUILTIN_TOOLS["opencode"]
        assert config["skills"] == ".opencode/skills"
        assert config["commands"] == ".opencode/commands"
        assert config["agents"] == ".opencode/agents"

    def test_codex_defined(self):
        assert "codex" in BUILTIN_TOOLS
        config = BUILTIN_TOOLS["codex"]
        assert config["skills"] == ".agents/skills"
        assert "commands" not in config
        assert "agents" not in config

    def test_codex_skills_only(self):
        """Verify codex adapter only supports skills."""
        adapter = get_tool("codex")
        assert adapter is not None
        assert adapter.supported_types == ["skills"]


class TestThreeTierResolution:
    """Tests for three-tier tool resolution."""

    def test_builtin_only(self):
        """Verify built-in tools are present."""
        tools = get_supported_tools()
        assert "claude-code" in tools
        assert "opencode" in tools
        assert "codex" in tools

    def test_global_override(self):
        """Verify global config overrides built-in."""
        global_tools = {
            "claude-code": {
                "skills": ".custom-claude/skills",
                "commands": ".custom-claude/commands",
            }
        }
        adapter = get_tool("claude-code", global_tools=global_tools)
        assert adapter is not None
        dest = adapter.get_destination("skills", Path("/repo"))
        assert dest == Path("/repo/.custom-claude/skills")
        # agents should NOT be supported (override is full replacement)
        assert "agents" not in adapter.supported_types

    def test_vault_override(self):
        """Verify vault config overrides global config."""
        global_tools = {"my-tool": {"skills": ".global/skills"}}
        vault_tools = {"my-tool": {"skills": ".vault/skills"}}
        adapter = get_tool("my-tool", global_tools=global_tools, vault_tools=vault_tools)
        assert adapter is not None
        dest = adapter.get_destination("skills", Path("/repo"))
        assert dest == Path("/repo/.vault/skills")

    def test_precedence_order(self):
        """Verify ascending precedence: built-in < global < vault."""
        global_tools = {"claude-code": {"skills": ".global/skills"}}
        vault_tools = {"claude-code": {"skills": ".vault/skills"}}
        adapter = get_tool("claude-code", global_tools=global_tools, vault_tools=vault_tools)
        assert adapter is not None
        dest = adapter.get_destination("skills", Path("/repo"))
        assert dest == Path("/repo/.vault/skills")

    def test_custom_tool_added(self):
        """Verify custom tools appear in supported tools."""
        global_tools = {"cursor": {"skills": ".cursor/skills"}}
        tools = get_supported_tools(global_tools=global_tools)
        assert "cursor" in tools

    def test_tool_source_builtin(self):
        """Verify source for built-in tool."""
        assert get_tool_source("claude-code") == "built-in"

    def test_tool_source_global(self):
        """Verify source for global config tool."""
        global_tools = {"cursor": {"skills": ".cursor/skills"}}
        assert get_tool_source("cursor", global_tools=global_tools) == "user global config"

    def test_tool_source_vault(self):
        """Verify source for vault tool."""
        vault_tools = {"custom": {"skills": ".custom/skills"}}
        source = get_tool_source("custom", vault_tools=vault_tools, vault_name="team-vault")
        assert source == "vault (team-vault)"


class TestAliasResolution:
    """Tests for alias resolution from tool definitions."""

    def test_builtin_alias(self):
        """Verify built-in aliases work."""
        assert resolve_tool_name("claude") == "claude-code"

    def test_custom_tool_alias(self):
        """Verify aliases from custom tool definitions."""
        global_tools = {"cursor": {"skills": ".cursor/skills", "aliases": ["cx"]}}
        assert resolve_tool_name("cx", extra_tools=global_tools) == "cursor"

    def test_vault_alias(self):
        """Verify aliases from vault tool definitions."""
        vault_tools = {"my-tool": {"skills": ".mt/skills", "aliases": ["mt"]}}
        assert resolve_tool_name("mt", vault_tools=vault_tools) == "my-tool"

    def test_get_aliases_for_custom_tool(self):
        """Verify get_aliases_for_tool works with custom tools."""
        global_tools = {"cursor": {"skills": ".cursor/skills", "aliases": ["cx", "cur"]}}
        aliases = get_aliases_for_tool("cursor", extra_tools=global_tools)
        assert "cx" in aliases
        assert "cur" in aliases


class TestToolConfigDirs:
    """Tests for get_tool_config_dirs."""

    def test_returns_per_type_paths(self):
        """Verify config dirs include per-type paths."""
        dirs = get_tool_config_dirs()
        assert "claude-code" in dirs
        assert dirs["claude-code"]["skills"] == ".claude/skills"
        assert dirs["claude-code"]["commands"] == ".claude/commands"

    def test_partial_tool_config_dirs(self):
        """Verify partial tool only includes supported types."""
        dirs = get_tool_config_dirs()
        assert "codex" in dirs
        assert "skills" in dirs["codex"]
        assert "commands" not in dirs["codex"]
        assert "agents" not in dirs["codex"]


class TestVaultMetadata:
    """Tests for vault.yaml read/write."""

    def test_load_missing_vault_yaml(self, tmp_path):
        """Verify missing vault.yaml returns empty defaults."""
        meta = load_vault_metadata(tmp_path)
        assert meta["name"] is None
        assert meta["tools"] == {}

    def test_save_and_load_vault_yaml(self, tmp_path):
        """Verify round-trip save and load."""
        save_vault_metadata(tmp_path, {"name": "team-vault", "tools": {
            "custom": {"skills": ".custom/skills"}
        }})
        meta = load_vault_metadata(tmp_path)
        assert meta["name"] == "team-vault"
        assert "custom" in meta["tools"]
        assert meta["tools"]["custom"]["skills"] == ".custom/skills"

    def test_save_omits_none_name(self, tmp_path):
        """Verify None name is not written to file."""
        save_vault_metadata(tmp_path, {"name": None, "tools": {}})
        content = (tmp_path / "vault.yaml").read_text()
        assert "name" not in content

    def test_vault_name_precedence(self, tmp_path):
        """Verify vault.yaml name can be loaded."""
        save_vault_metadata(tmp_path, {"name": "portable-name"})
        meta = load_vault_metadata(tmp_path)
        assert meta["name"] == "portable-name"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
