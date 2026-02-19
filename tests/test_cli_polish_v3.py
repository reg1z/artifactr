"""Tests for CLI polish v3 changes."""

import json
from pathlib import Path
from unittest import mock

import pytest
import yaml

from artifactr.catalog import _next_auto_name, create_vault_directory, init_vault
from artifactr.cli import create_parser
from artifactr.creator import (
    _find_by_frontmatter_name,
    _parse_frontmatter_name,
    create_artifact,
    resolve_edit_target,
)
from artifactr.scanner import discover_artifacts_by_structure


class TestVaultNaming:
    """11.1 - Test vault naming produces vault-N pattern."""

    def test_first_vault_auto_name(self):
        config = {"vault_names": {}}
        assert _next_auto_name(config) == "vault-1"

    def test_incrementing_auto_name(self):
        config = {"vault_names": {"/a": "vault-3", "/b": "vault-1"}}
        assert _next_auto_name(config) == "vault-4"

    def test_ignores_old_llm_vault_pattern(self):
        config = {"vault_names": {"/a": "llm-vault-5"}}
        assert _next_auto_name(config) == "vault-1"


class TestVaultInitPrompt:
    """11.2 - Test vault init prompts on missing directory and respects --yes."""

    @mock.patch("artifactr.catalog.save_config")
    @mock.patch("artifactr.catalog.load_config")
    def test_missing_dir_returns_signal(self, mock_load, mock_save, tmp_path):
        vault_dir = tmp_path / "nonexistent"
        mock_load.return_value = {
            "vaults": [], "vault_names": {}, "default_vault": None, "default_tool": "claude-code",
        }
        result = init_vault(str(vault_dir))
        assert result["dir_missing"] is True
        assert result["created"] is False

    @mock.patch("artifactr.catalog.save_config")
    @mock.patch("artifactr.catalog.load_config")
    def test_create_vault_directory_after_confirm(self, mock_load, mock_save, tmp_path):
        vault_dir = tmp_path / "to-create"
        mock_load.return_value = {
            "vaults": [], "vault_names": {}, "default_vault": None, "default_tool": "claude-code",
        }
        result = create_vault_directory(str(vault_dir))
        assert result["created"] is True
        assert (vault_dir / "skills").is_dir()

    def test_yes_flag_parsed(self):
        parser = create_parser()
        args = parser.parse_args(["vault", "init", "/path", "-y"])
        assert args.yes is True

    def test_existing_dir_no_signal(self, tmp_path):
        vault_dir = tmp_path / "exists"
        vault_dir.mkdir()
        with mock.patch("artifactr.catalog.save_config"), \
             mock.patch("artifactr.catalog.load_config") as mock_load:
            mock_load.return_value = {
                "vaults": [], "vault_names": {}, "default_vault": None, "default_tool": "claude-code",
            }
            result = init_vault(str(vault_dir))
            assert result["dir_missing"] is False


class TestEditFrontmatterFallback:
    """11.3 - Test edit frontmatter fallback."""

    def test_parse_frontmatter_name(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("---\nname: My Artifact\ndescription: test\n---\nContent here\n")
        assert _parse_frontmatter_name(f) == "My Artifact"

    def test_parse_frontmatter_name_quoted(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text('---\nname: "Quoted Name"\n---\n')
        assert _parse_frontmatter_name(f) == "Quoted Name"

    def test_parse_frontmatter_no_name(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("---\ndescription: test\n---\n")
        assert _parse_frontmatter_name(f) is None

    def test_parse_frontmatter_no_frontmatter(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("Just content\n")
        assert _parse_frontmatter_name(f) is None

    def test_find_by_frontmatter_name_agent(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "alpha.md").write_text("---\nname: helper\n---\n")
        (agents_dir / "beta.md").write_text("---\nname: other\n---\n")
        result = _find_by_frontmatter_name("agent", "helper", tmp_path)
        assert result == agents_dir / "alpha.md"

    def test_find_by_frontmatter_name_skill(self, tmp_path):
        skills_dir = tmp_path / "skills"
        (skills_dir / "my-skill").mkdir(parents=True)
        (skills_dir / "my-skill" / "SKILL.md").write_text("---\nname: greet\n---\n")
        result = _find_by_frontmatter_name("skill", "greet", tmp_path)
        assert result == skills_dir / "my-skill" / "SKILL.md"

    def test_find_by_frontmatter_name_alphabetical_tiebreak(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "aaa.md").write_text("---\nname: dup\n---\n")
        (agents_dir / "zzz.md").write_text("---\nname: dup\n---\n")
        result = _find_by_frontmatter_name("agent", "dup", tmp_path)
        assert result == agents_dir / "aaa.md"

    def test_folder_match_takes_priority(self, tmp_path):
        """Folder match should be returned even if frontmatter name matches elsewhere."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "helper.md").write_text("---\nname: something-else\n---\n")
        (agents_dir / "other.md").write_text("---\nname: helper\n---\n")

        with mock.patch("artifactr.creator.get_default_vault", return_value=str(tmp_path)), \
             mock.patch("artifactr.creator.get_vault_by_name_or_path", return_value=str(tmp_path)):
            result = resolve_edit_target("agent", "helper")
            assert result["success"] is True
            assert Path(result["path"]) == agents_dir / "helper.md"

    def test_frontmatter_fallback_when_no_folder_match(self, tmp_path):
        """Frontmatter name should be used when no folder/file match exists."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "my-helper.md").write_text("---\nname: helper\n---\n")

        with mock.patch("artifactr.creator.get_default_vault", return_value=str(tmp_path)), \
             mock.patch("artifactr.creator.get_vault_by_name_or_path", return_value=str(tmp_path)):
            result = resolve_edit_target("agent", "helper")
            assert result["success"] is True
            assert Path(result["path"]) == agents_dir / "my-helper.md"


class TestCreateAgentDisplayName:
    """11.4 - Test create agent with --name produces correct frontmatter."""

    def test_agent_with_display_name(self, tmp_path):
        target = tmp_path / "agents" / "my-bot.md"
        result = create_artifact(
            artifact_type="agent",
            name="Cool Bot",
            description="A cool bot",
            target_path=target,
        )
        assert result["success"] is True
        content = target.read_text()
        assert "name: Cool Bot" in content

    def test_agent_without_display_name(self, tmp_path):
        target = tmp_path / "agents" / "my-bot.md"
        result = create_artifact(
            artifact_type="agent",
            name=None,
            description="A bot",
            target_path=target,
        )
        assert result["success"] is True
        content = target.read_text()
        assert "name:" not in content
        assert "description: A bot" in content

    def test_create_agent_name_flag_parsed(self):
        parser = create_parser()
        args = parser.parse_args(["create", "agent", "my-bot", "-d", "desc", "-n", "Cool Bot"])
        assert args.display_name == "Cool Bot"


class TestProjectImportNonGit:
    """11.5 - Test project import with non-git target."""

    def test_yes_flag_parsed(self):
        parser = create_parser()
        args = parser.parse_args(["project", "import", "--yes"])
        assert args.yes is True

    def test_import_artifacts_no_git_error(self, tmp_path):
        """import_artifacts should not error on non-git target anymore."""
        from artifactr.importer import import_artifacts

        target = tmp_path / "not-git"
        target.mkdir()

        with mock.patch("artifactr.importer.get_default_vault", return_value=str(tmp_path)), \
             mock.patch("artifactr.importer.get_supported_tools", return_value=[]), \
             mock.patch("artifactr.importer.list_vaults", return_value={"vault_names": {}}):
            result = import_artifacts(str(target), tools=[])
            assert result["success"] is True


class TestStoreGlobalAndTools:
    """11.6 - Test store --global and --tools flags."""

    def test_global_flag_parsed(self):
        parser = create_parser()
        args = parser.parse_args(["store", "--global"])
        assert args.global_store is True
        assert args.target_dir is None

    def test_tools_flag_parsed(self):
        parser = create_parser()
        args = parser.parse_args(["store", "--global", "--tools", "claude-code"])
        assert args.tools == "claude-code"

    def test_target_dir_optional(self):
        parser = create_parser()
        args = parser.parse_args(["store", "./some-dir"])
        assert args.target_dir == "./some-dir"
        assert args.global_store is False


class TestSpelunkDepthScanning:
    """11.7 - Test spelunk --depth scanning finds nested artifact directories."""

    def test_discovers_skills_at_depth_1(self, tmp_path):
        sub = tmp_path / "project"
        sub.mkdir()
        skills = sub / "skills" / "my-skill"
        skills.mkdir(parents=True)
        (skills / "SKILL.md").write_text("---\nname: my-skill\n---\n")

        artifacts = discover_artifacts_by_structure(tmp_path, depth=2)
        assert len(artifacts) == 1
        assert artifacts[0]["name"] == "my-skill"
        assert artifacts[0]["type"] == "skill"
        assert artifacts[0]["tool"] == "directory"

    def test_discovers_commands_and_agents(self, tmp_path):
        cmds = tmp_path / "commands"
        cmds.mkdir()
        (cmds / "deploy.md").write_text("---\ndescription: deploy\n---\n")
        agents = tmp_path / "agents"
        agents.mkdir()
        (agents / "helper.md").write_text("---\nname: helper\n---\n")

        artifacts = discover_artifacts_by_structure(tmp_path, depth=0)
        assert len(artifacts) == 2
        types = {a["type"] for a in artifacts}
        assert types == {"command", "agent"}

    def test_respects_depth_limit(self, tmp_path):
        # Create artifact at depth 3 (too deep for depth=1)
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        skills = deep / "skills" / "deep-skill"
        skills.mkdir(parents=True)
        (skills / "SKILL.md").write_text("---\nname: deep\n---\n")

        artifacts = discover_artifacts_by_structure(tmp_path, depth=1)
        assert len(artifacts) == 0

        artifacts = discover_artifacts_by_structure(tmp_path, depth=3)
        assert len(artifacts) == 1

    def test_depth_flag_parsed(self):
        parser = create_parser()
        args = parser.parse_args(["spelunk", "./dir", "--depth", "5"])
        assert args.depth == 5

    def test_depth_default(self):
        parser = create_parser()
        args = parser.parse_args(["spelunk", "./dir"])
        assert args.depth == 2


class TestSpelunkOutputFormats:
    """11.8 - Test spelunk --format outputs valid json, yaml, and markdown."""

    def test_format_flag_parsed(self):
        parser = create_parser()
        for fmt in ["human", "json", "yaml", "md", "markdown"]:
            args = parser.parse_args(["spelunk", "--format", fmt])
            assert args.format == fmt

    def test_format_default_human(self):
        parser = create_parser()
        args = parser.parse_args(["spelunk"])
        assert args.format == "human"

    def test_json_output(self):
        from artifactr.cli import _format_spelunk_json

        artifacts = [
            {"name": "test", "type": "skill", "path": Path("/a/b"), "tool": "vault"},
        ]
        output = _format_spelunk_json(artifacts)
        parsed = json.loads(output)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "test"
        assert parsed[0]["type"] == "skill"

    def test_yaml_output(self):
        from artifactr.cli import _format_spelunk_yaml

        artifacts = [
            {"name": "test", "type": "agent", "path": Path("/x/y"), "tool": "claude-code"},
        ]
        output = _format_spelunk_yaml(artifacts)
        parsed = yaml.safe_load(output)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "test"

    def test_markdown_output(self):
        from artifactr.cli import _format_spelunk_markdown

        artifacts = [
            {"name": "test", "type": "command", "path": Path("/c/d"), "tool": "directory"},
        ]
        output = _format_spelunk_markdown(artifacts)
        assert "| Name |" in output
        assert "| test |" in output

    def test_empty_json(self):
        from artifactr.cli import _format_spelunk_json

        output = _format_spelunk_json([])
        assert json.loads(output) == []

    def test_empty_markdown(self):
        from artifactr.cli import _format_spelunk_markdown

        output = _format_spelunk_markdown([])
        assert "| Name |" in output
        lines = output.strip().split("\n")
        assert len(lines) == 2  # header + separator, no data rows


class TestNewAliases:
    """11.9 - Test all new aliases resolve correctly."""

    def test_vault_shorthand_V(self):
        parser = create_parser()
        # Commands that use multi-vault (vaults as list)
        for cmd_args in [
            ["ls", "-V", "my-vault"],
            ["store", "./dir", "-V", "my-vault"],
            ["create", "skill", "x", "-d", "d", "-V", "my-vault"],
            ["create", "command", "x", "-d", "d", "-V", "my-vault"],
            ["create", "agent", "x", "-d", "d", "-V", "my-vault"],
            ["project", "import", "-V", "my-vault"],
            ["config", "import", "-V", "my-vault"],
            ["tool", "add", "x", "--skills", "s", "-V", "my-vault"],
            ["tool", "ls", "-V", "my-vault"],
        ]:
            args = parser.parse_args(cmd_args)
            assert getattr(args, "vaults", None) == ["my-vault"], f"Failed for {cmd_args}"
        # Commands that use single vault (vault as str)
        for cmd_args in [
            ["rm", "x", "-V", "my-vault"],
            ["edit", "skill", "x", "-V", "my-vault"],
            ["tool", "rm", "x", "-V", "my-vault"],
        ]:
            args = parser.parse_args(cmd_args)
            assert getattr(args, "vault", None) == "my-vault", f"Failed for {cmd_args}"

    def test_vault_create_cr_aliases(self):
        parser = create_parser()
        for alias in ["create", "cr"]:
            args = parser.parse_args(["vault", alias, "/path"])
            assert args.target_dir == "/path"

    def test_edit_type_aliases(self):
        parser = create_parser()
        for alias in [
            "s", "sk", "c", "cmd", "com", "a", "agt", "ag",
        ]:
            args = parser.parse_args(["edit", alias, "test-name"])
            assert args.artifact == [alias, "test-name"]

    def test_create_subcommand_aliases(self):
        parser = create_parser()
        for alias in ["skill", "s", "sk"]:
            args = parser.parse_args(["create", alias, "test", "-d", "desc"])
            assert args.create_command == alias

        for alias in ["command", "c", "cmd", "com"]:
            args = parser.parse_args(["create", alias, "test", "-d", "desc"])
            assert args.create_command == alias

        for alias in ["agent", "a", "agt", "ag"]:
            args = parser.parse_args(["create", alias, "test", "-d", "desc"])
            assert args.create_command == alias


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
