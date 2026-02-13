"""Tests for creator module."""

from pathlib import Path
from unittest import mock

import pytest
import yaml

from artifactr.creator import create_skill, resolve_project_target, resolve_vault_target


class TestCreateSkill:
    """Tests for create_skill function."""

    def test_creates_skill_md(self, tmp_path):
        """Verify SKILL.md is created with correct frontmatter."""
        target = tmp_path / "skills" / "my-skill"
        result = create_skill(
            name="my-skill",
            description="A helpful skill",
            target_path=target,
        )

        assert result["success"] is True
        skill_file = target / "SKILL.md"
        assert skill_file.exists()

        content = skill_file.read_text()
        assert content.startswith("---\n")
        assert "name: my-skill" in content
        assert "description: A helpful skill" in content

    def test_creates_skill_with_content(self, tmp_path):
        """Verify markdown body is included after frontmatter."""
        target = tmp_path / "skills" / "my-skill"
        result = create_skill(
            name="my-skill",
            description="A skill",
            content="Instructions here",
            target_path=target,
        )

        assert result["success"] is True
        text = (target / "SKILL.md").read_text()
        # Content should appear after the closing ---
        parts = text.split("---")
        assert len(parts) >= 3
        body = parts[2]
        assert "Instructions here" in body

    def test_creates_skill_with_extra_fields(self, tmp_path):
        """Verify extra fields are included in frontmatter."""
        target = tmp_path / "skills" / "my-skill"
        result = create_skill(
            name="my-skill",
            description="A skill",
            extra_fields={"author": "Jane", "version": "1.0"},
            target_path=target,
        )

        assert result["success"] is True
        text = (target / "SKILL.md").read_text()
        assert "author: Jane" in text
        assert "version: '1.0'" in text or 'version: "1.0"' in text

    def test_overwrite_protection(self, tmp_path):
        """Verify error when skill directory already exists."""
        target = tmp_path / "skills" / "my-skill"
        target.mkdir(parents=True)

        result = create_skill(
            name="my-skill",
            description="A skill",
            target_path=target,
        )

        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_no_target_path(self):
        """Verify error when no target path is provided."""
        result = create_skill(name="my-skill")
        assert result["success"] is False
        assert "No target path" in result["error"]

    def test_creates_parent_directories(self, tmp_path):
        """Verify parent directories are created automatically."""
        target = tmp_path / "deep" / "nested" / "skills" / "my-skill"
        result = create_skill(
            name="my-skill",
            description="A skill",
            target_path=target,
        )

        assert result["success"] is True
        assert (target / "SKILL.md").exists()

    def test_frontmatter_is_valid_yaml(self, tmp_path):
        """Verify the frontmatter can be parsed as valid YAML."""
        target = tmp_path / "skills" / "my-skill"
        create_skill(
            name="my-skill",
            description="A skill",
            extra_fields={"user-invocable": "true"},
            target_path=target,
        )

        text = (target / "SKILL.md").read_text()
        # Extract YAML between --- markers
        parts = text.split("---")
        parsed = yaml.safe_load(parts[1])
        assert parsed["name"] == "my-skill"
        assert parsed["description"] == "A skill"

    def test_returns_path_on_success(self, tmp_path):
        """Verify the result contains the path to the created file."""
        target = tmp_path / "skills" / "my-skill"
        result = create_skill(
            name="my-skill",
            description="A skill",
            target_path=target,
        )

        assert result["path"] == str(target / "SKILL.md")


class TestResolveVaultTarget:
    """Tests for resolve_vault_target function."""

    @mock.patch("artifactr.creator.get_default_vault")
    def test_default_vault(self, mock_default):
        """Verify default vault is used when no vault specified."""
        mock_default.return_value = "/path/to/vault"
        result = resolve_vault_target("my-skill")

        assert result["success"] is True
        assert result["path"] == Path("/path/to/vault/skills/my-skill")

    @mock.patch("artifactr.creator.get_default_vault")
    def test_no_default_vault(self, mock_default):
        """Verify error when no default vault is set."""
        mock_default.return_value = None
        result = resolve_vault_target("my-skill")

        assert result["success"] is False
        assert "No default vault" in result["error"]

    @mock.patch("artifactr.creator.get_vault_by_name_or_path")
    def test_explicit_vault(self, mock_vault):
        """Verify explicit vault name is resolved."""
        mock_vault.return_value = "/path/to/favorites"
        result = resolve_vault_target("my-skill", vault="favorites")

        assert result["success"] is True
        assert result["path"] == Path("/path/to/favorites/skills/my-skill")

    @mock.patch("artifactr.creator.get_vault_by_name_or_path")
    def test_invalid_vault(self, mock_vault):
        """Verify error when vault is not found."""
        mock_vault.return_value = None
        result = resolve_vault_target("my-skill", vault="nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"]


class TestResolveProjectTarget:
    """Tests for resolve_project_target function."""

    @mock.patch("artifactr.creator.get_tool")
    @mock.patch("artifactr.creator.get_supported_tools")
    def test_default_tools(self, mock_supported, mock_get_tool):
        """Verify all supported tools are used when none specified."""
        mock_supported.return_value = ["claude-code", "opencode"]

        mock_claude = mock.MagicMock()
        mock_claude.supported_types = ["skills", "commands", "agents"]
        mock_claude.get_destination.return_value = Path.cwd() / ".claude" / "skills"
        mock_open = mock.MagicMock()
        mock_open.supported_types = ["skills", "commands", "agents"]
        mock_open.get_destination.return_value = Path.cwd() / ".opencode" / "skills"

        def get_tool_side_effect(name):
            return {"claude-code": mock_claude, "opencode": mock_open}.get(name)

        mock_get_tool.side_effect = get_tool_side_effect

        result = resolve_project_target("my-skill")

        assert result["success"] is True
        assert len(result["paths"]) == 2

    @mock.patch("artifactr.creator.get_tool")
    def test_explicit_tools(self, mock_get_tool):
        """Verify only specified tools are used."""
        mock_claude = mock.MagicMock()
        mock_claude.supported_types = ["skills", "commands", "agents"]
        mock_claude.get_destination.return_value = Path.cwd() / ".claude" / "skills"
        mock_get_tool.return_value = mock_claude

        result = resolve_project_target("my-skill", tools=["claude-code"])

        assert result["success"] is True
        assert len(result["paths"]) == 1

    @mock.patch("artifactr.creator.get_tool")
    def test_unknown_tool(self, mock_get_tool):
        """Verify error for unknown tool names."""
        mock_get_tool.return_value = None

        result = resolve_project_target("my-skill", tools=["unknown-tool"])

        assert result["success"] is False
        assert "Unknown tool" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
