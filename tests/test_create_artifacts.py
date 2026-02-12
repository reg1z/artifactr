"""Tests for command and agent creation."""

from pathlib import Path
from unittest import mock

import pytest
import yaml

from artifactr.cli import create_parser
from artifactr.creator import create_artifact, resolve_vault_target, resolve_project_target


class TestCreateCommand:
    """Tests for command creation (file-based, no name in frontmatter)."""

    def test_creates_command_file(self, tmp_path):
        """Verify command .md file is created."""
        target = tmp_path / "commands" / "my-cmd.md"
        result = create_artifact(
            artifact_type="command",
            name="my-cmd",
            description="Run deployment",
            target_path=target,
        )

        assert result["success"] is True
        assert target.exists()
        assert target.is_file()

    def test_command_no_name_in_frontmatter(self, tmp_path):
        """Verify command frontmatter does NOT contain name field."""
        target = tmp_path / "commands" / "deploy.md"
        create_artifact(
            artifact_type="command",
            name="deploy",
            description="Deploy to prod",
            target_path=target,
        )

        text = target.read_text()
        parts = text.split("---")
        parsed = yaml.safe_load(parts[1])
        assert "name" not in parsed
        assert parsed["description"] == "Deploy to prod"

    def test_command_with_content(self, tmp_path):
        """Verify markdown body is included."""
        target = tmp_path / "commands" / "my-cmd.md"
        create_artifact(
            artifact_type="command",
            name="my-cmd",
            description="desc",
            content="Instructions here",
            target_path=target,
        )

        text = target.read_text()
        assert "Instructions here" in text

    def test_command_with_extra_fields(self, tmp_path):
        """Verify extra fields in frontmatter."""
        target = tmp_path / "commands" / "my-cmd.md"
        create_artifact(
            artifact_type="command",
            name="my-cmd",
            description="desc",
            extra_fields={"key": "value"},
            target_path=target,
        )

        text = target.read_text()
        parts = text.split("---")
        parsed = yaml.safe_load(parts[1])
        assert parsed["key"] == "value"

    def test_command_overwrite_protection(self, tmp_path):
        """Verify error when command file already exists."""
        target = tmp_path / "commands" / "my-cmd.md"
        target.parent.mkdir(parents=True)
        target.write_text("existing")

        result = create_artifact(
            artifact_type="command",
            name="my-cmd",
            description="desc",
            target_path=target,
        )

        assert result["success"] is False
        assert "already exists" in result["error"]


class TestCreateAgent:
    """Tests for agent creation (file-based, name in frontmatter)."""

    def test_creates_agent_file(self, tmp_path):
        """Verify agent .md file is created."""
        target = tmp_path / "agents" / "my-agent.md"
        result = create_artifact(
            artifact_type="agent",
            name="my-agent",
            description="Handles reviews",
            target_path=target,
        )

        assert result["success"] is True
        assert target.exists()

    def test_agent_name_in_frontmatter(self, tmp_path):
        """Verify agent frontmatter contains name field."""
        target = tmp_path / "agents" / "code-reviewer.md"
        create_artifact(
            artifact_type="agent",
            name="code-reviewer",
            description="Reviews code",
            target_path=target,
        )

        text = target.read_text()
        parts = text.split("---")
        parsed = yaml.safe_load(parts[1])
        assert parsed["name"] == "code-reviewer"
        assert parsed["description"] == "Reviews code"

    def test_agent_with_content_and_fields(self, tmp_path):
        """Verify agent with content and extra fields."""
        target = tmp_path / "agents" / "my-agent.md"
        create_artifact(
            artifact_type="agent",
            name="my-agent",
            description="desc",
            content="Body text",
            extra_fields={"model": "sonnet"},
            target_path=target,
        )

        text = target.read_text()
        parts = text.split("---")
        parsed = yaml.safe_load(parts[1])
        assert parsed["model"] == "sonnet"
        assert "Body text" in text

    def test_agent_overwrite_protection(self, tmp_path):
        """Verify error when agent file already exists."""
        target = tmp_path / "agents" / "my-agent.md"
        target.parent.mkdir(parents=True)
        target.write_text("existing")

        result = create_artifact(
            artifact_type="agent",
            name="my-agent",
            description="desc",
            target_path=target,
        )

        assert result["success"] is False
        assert "already exists" in result["error"]


class TestResolveVaultTargetGeneralized:
    """Tests for generalized resolve_vault_target."""

    @mock.patch("artifactr.creator.get_default_vault")
    def test_command_vault_target(self, mock_default):
        """Verify command resolves to .md file in commands subdir."""
        mock_default.return_value = "/path/to/vault"
        result = resolve_vault_target("my-cmd", artifact_type="command")

        assert result["success"] is True
        assert result["path"] == Path("/path/to/vault/commands/my-cmd.md")

    @mock.patch("artifactr.creator.get_default_vault")
    def test_agent_vault_target(self, mock_default):
        """Verify agent resolves to .md file in agents subdir."""
        mock_default.return_value = "/path/to/vault"
        result = resolve_vault_target("my-agent", artifact_type="agent")

        assert result["success"] is True
        assert result["path"] == Path("/path/to/vault/agents/my-agent.md")

    @mock.patch("artifactr.creator.get_default_vault")
    def test_skill_vault_target_unchanged(self, mock_default):
        """Verify skill still resolves to directory."""
        mock_default.return_value = "/path/to/vault"
        result = resolve_vault_target("my-skill", artifact_type="skill")

        assert result["success"] is True
        assert result["path"] == Path("/path/to/vault/skills/my-skill")


class TestCreateCommandCLIParsing:
    """Tests for create command CLI argument parsing."""

    def test_command_name_parsed(self):
        """Verify command name is parsed."""
        parser = create_parser()
        args = parser.parse_args(["create", "command", "my-cmd"])
        assert args.create_command == "command"
        assert args.command_name == "my-cmd"

    def test_command_description_flag(self):
        """Verify -d flag is parsed."""
        parser = create_parser()
        args = parser.parse_args(["create", "command", "my-cmd", "-d", "A command"])
        assert args.description == "A command"

    def test_command_here_flag(self):
        """Verify --here flag works for commands."""
        parser = create_parser()
        args = parser.parse_args(["create", "command", "my-cmd", "-H"])
        assert args.here is True


class TestCreateAgentCLIParsing:
    """Tests for create agent CLI argument parsing."""

    def test_agent_name_parsed(self):
        """Verify agent name is parsed."""
        parser = create_parser()
        args = parser.parse_args(["create", "agent", "my-agent"])
        assert args.create_command == "agent"
        assert args.agent_name == "my-agent"

    def test_agent_description_flag(self):
        """Verify -d flag is parsed."""
        parser = create_parser()
        args = parser.parse_args(["create", "agent", "my-agent", "-d", "An agent"])
        assert args.description == "An agent"

    def test_agent_field_flags(self):
        """Verify -D field flags work for agents."""
        parser = create_parser()
        args = parser.parse_args([
            "create", "agent", "my-agent", "-D", "model=sonnet",
        ])
        assert args.field == ["model=sonnet"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
