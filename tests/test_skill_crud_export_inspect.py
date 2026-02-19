"""Tests for skill-crud-export-inspect: edit enhancements, ls artifact listing,
art cat, art inspect, art export, and art store zip support."""

import io
import sys
import zipfile
from pathlib import Path
from unittest import mock

import pytest

from artifactr.cli import (
    _parse_artifact_specifier,
    _list_skill_files,
    _detect_zip_artifact_type,
    create_parser,
    handle_cat,
    handle_edit,
    handle_export,
    handle_inspect,
    handle_list,
    handle_store,
)
from artifactr.creator import find_artifact_in_vault


# ---------------------------------------------------------------------------
# _parse_artifact_specifier
# ---------------------------------------------------------------------------


class TestParseArtifactSpecifier:
    def test_name_only(self):
        t, n, s = _parse_artifact_specifier("my-skill")
        assert t is None
        assert n == "my-skill"
        assert s is None

    def test_type_prefix_skill(self):
        t, n, s = _parse_artifact_specifier("skill/my-skill")
        assert t == "skill"
        assert n == "my-skill"
        assert s is None

    def test_type_prefix_short_sk(self):
        t, n, s = _parse_artifact_specifier("sk/my-skill")
        assert t == "skill"
        assert n == "my-skill"
        assert s is None

    def test_type_prefix_command(self):
        t, n, s = _parse_artifact_specifier("c/my-cmd")
        assert t == "command"
        assert n == "my-cmd"
        assert s is None

    def test_type_prefix_agent(self):
        t, n, s = _parse_artifact_specifier("agt/my-agent")
        assert t == "agent"
        assert n == "my-agent"
        assert s is None

    def test_subpath(self):
        t, n, s = _parse_artifact_specifier("my-skill/references/hooks.md")
        assert t is None
        assert n == "my-skill"
        assert s == "references/hooks.md"

    def test_type_prefix_and_subpath(self):
        t, n, s = _parse_artifact_specifier("skill/my-skill/references/hooks.md")
        assert t == "skill"
        assert n == "my-skill"
        assert s == "references/hooks.md"

    def test_short_alias_with_subpath(self):
        t, n, s = _parse_artifact_specifier("sk/my-skill/sub/path.md")
        assert t == "skill"
        assert n == "my-skill"
        assert s == "sub/path.md"


# ---------------------------------------------------------------------------
# find_artifact_in_vault
# ---------------------------------------------------------------------------


class TestFindArtifactInVault:
    def test_finds_skill_by_name(self, tmp_path):
        vault = tmp_path / "vault"
        skill_file = vault / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")

        matches = find_artifact_in_vault("my-skill", str(vault))
        assert len(matches) == 1
        assert matches[0]["type"] == "skill"
        assert matches[0]["path"] == skill_file

    def test_finds_command_by_name(self, tmp_path):
        vault = tmp_path / "vault"
        cmd_file = vault / "commands" / "my-cmd.md"
        cmd_file.parent.mkdir(parents=True)
        cmd_file.write_text("---\ndescription: test\n---\n")

        matches = find_artifact_in_vault("my-cmd", str(vault))
        assert len(matches) == 1
        assert matches[0]["type"] == "command"

    def test_finds_by_frontmatter_name(self, tmp_path):
        vault = tmp_path / "vault"
        skill_file = vault / "skills" / "my-folder" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: Display Name\n---\n")

        matches = find_artifact_in_vault("Display Name", str(vault))
        assert len(matches) == 1
        assert matches[0]["type"] == "skill"

    def test_filters_by_type(self, tmp_path):
        vault = tmp_path / "vault"
        cmd_file = vault / "commands" / "my-thing.md"
        cmd_file.parent.mkdir(parents=True)
        cmd_file.write_text("---\ndescription: test\n---\n")
        skill_file = vault / "skills" / "my-thing" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-thing\n---\n")

        matches = find_artifact_in_vault("my-thing", str(vault), artifact_type="command")
        assert len(matches) == 1
        assert matches[0]["type"] == "command"

    def test_returns_empty_when_not_found(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        matches = find_artifact_in_vault("nonexistent", str(vault))
        assert matches == []

    def test_ambiguous_returns_multiple(self, tmp_path):
        vault = tmp_path / "vault"
        cmd_file = vault / "commands" / "shared.md"
        cmd_file.parent.mkdir(parents=True)
        cmd_file.write_text("---\ndescription: test\n---\n")
        skill_file = vault / "skills" / "shared" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: shared\n---\n")

        matches = find_artifact_in_vault("shared", str(vault))
        assert len(matches) == 2


# ---------------------------------------------------------------------------
# _list_skill_files
# ---------------------------------------------------------------------------


class TestListSkillFiles:
    def test_skill_md_first(self, tmp_path):
        skill = tmp_path / "my-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("main")
        (skill / "refs" / "a.md").parent.mkdir()
        (skill / "refs" / "a.md").write_text("ref")

        files = _list_skill_files(skill)
        assert files[0].name == "SKILL.md"
        assert len(files) == 2

    def test_only_skill_md(self, tmp_path):
        skill = tmp_path / "my-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("main")

        files = _list_skill_files(skill)
        assert files == [skill / "SKILL.md"]


# ---------------------------------------------------------------------------
# handle_edit — unified specifier and auto-detection
# ---------------------------------------------------------------------------


class TestHandleEditUnifiedSpecifier:
    @mock.patch("artifactr.creator.get_default_vault")
    def test_old_two_positional_form(self, mock_default, tmp_path):
        """art edit skill my-skill (old form) still works."""
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = ["skill", "my-skill"]
        args.vault = None
        args.here = False
        args.tools = None
        args.interactive = False
        args.main = False
        args.new_file = None

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)
            result = handle_edit(args)

        assert result == 0
        called_path = Path(mock_run.call_args[0][0][1])
        assert called_path == skill_file

    @mock.patch("artifactr.creator.get_default_vault")
    @mock.patch("artifactr.cli.get_default_vault")
    def test_unified_specifier_auto_detect(self, mock_cli_default, mock_creator_default, tmp_path):
        """art edit my-skill (no type) auto-detects the skill."""
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        mock_cli_default.return_value = str(vault_dir)
        mock_creator_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = ["my-skill"]
        args.vault = None
        args.here = False
        args.tools = None
        args.interactive = False
        args.main = False
        args.new_file = None

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)
            with mock.patch("sys.stdin") as mock_stdin:
                mock_stdin.isatty.return_value = False
                result = handle_edit(args)

        assert result == 0

    @mock.patch("artifactr.cli.get_default_vault")
    def test_ambiguous_name_errors(self, mock_default, tmp_path):
        """Ambiguous name (multiple types) should print error and return 1."""
        vault_dir = tmp_path / "vault"
        # Create both skill and command with same name
        skill_file = vault_dir / "skills" / "shared" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: shared\n---\n")
        cmd_file = vault_dir / "commands" / "shared.md"
        cmd_file.parent.mkdir(parents=True)
        cmd_file.write_text("---\ndescription: test\n---\n")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = ["shared"]
        args.vault = None
        args.here = False
        args.tools = None
        args.interactive = False
        args.main = False
        args.new_file = None

        result = handle_edit(args)
        assert result == 1


# ---------------------------------------------------------------------------
# handle_edit — sub-path support
# ---------------------------------------------------------------------------


class TestHandleEditSubPath:
    @mock.patch("artifactr.creator.get_default_vault")
    def test_subpath_opens_file(self, mock_default, tmp_path):
        """art edit my-skill/refs/hooks.md opens the sub-path file."""
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        ref_file = vault_dir / "skills" / "my-skill" / "refs" / "hooks.md"
        ref_file.parent.mkdir(parents=True)
        ref_file.write_text("hook content")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = ["sk/my-skill/refs/hooks.md"]
        args.vault = None
        args.here = False
        args.tools = None
        args.interactive = False
        args.main = False
        args.new_file = None

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)
            result = handle_edit(args)

        assert result == 0
        called_path = Path(mock_run.call_args[0][0][1])
        assert called_path == ref_file

    @mock.patch("artifactr.creator.get_default_vault")
    def test_subpath_not_found_errors(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = ["my-skill/nonexistent.md"]
        args.vault = None
        args.here = False
        args.tools = None
        args.interactive = False
        args.main = False
        args.new_file = None

        result = handle_edit(args)
        assert result == 1

    @mock.patch("artifactr.creator.get_default_vault")
    def test_subpath_on_command_errors(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        cmd_file = vault_dir / "commands" / "my-cmd.md"
        cmd_file.parent.mkdir(parents=True)
        cmd_file.write_text("---\ndescription: test\n---\n")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = ["c/my-cmd/some-file.md"]
        args.vault = None
        args.here = False
        args.tools = None
        args.interactive = False
        args.main = False
        args.new_file = None

        result = handle_edit(args)
        assert result == 1


# ---------------------------------------------------------------------------
# handle_edit — --new-file support
# ---------------------------------------------------------------------------


class TestHandleEditNewFile:
    @mock.patch("artifactr.creator.get_default_vault")
    def test_new_file_created(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = ["skill", "my-skill"]
        args.vault = None
        args.here = False
        args.tools = None
        args.interactive = False
        args.main = False
        args.new_file = "refs/new.md"

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)
            result = handle_edit(args)

        assert result == 0
        new_file = vault_dir / "skills" / "my-skill" / "refs" / "new.md"
        assert new_file.exists()

    @mock.patch("artifactr.creator.get_default_vault")
    def test_new_file_collision_errors(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        existing = vault_dir / "skills" / "my-skill" / "existing.md"
        existing.write_text("already here")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = ["skill", "my-skill"]
        args.vault = None
        args.here = False
        args.tools = None
        args.interactive = False
        args.main = False
        args.new_file = "existing.md"

        result = handle_edit(args)
        assert result == 1

    @mock.patch("artifactr.creator.get_default_vault")
    def test_new_file_on_command_errors(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        cmd_file = vault_dir / "commands" / "my-cmd.md"
        cmd_file.parent.mkdir(parents=True)
        cmd_file.write_text("---\ndescription: test\n---\n")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = ["c/my-cmd"]
        args.vault = None
        args.here = False
        args.tools = None
        args.interactive = False
        args.main = False
        args.new_file = "some-file.md"

        result = handle_edit(args)
        assert result == 1


# ---------------------------------------------------------------------------
# handle_edit — interactive picker (non-TTY fallback)
# ---------------------------------------------------------------------------


class TestHandleEditPicker:
    @mock.patch("artifactr.creator.get_default_vault")
    def test_non_tty_opens_skill_md_directly(self, mock_default, tmp_path):
        """Non-TTY stdin should bypass picker and open SKILL.md."""
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        extra = vault_dir / "skills" / "my-skill" / "extra.md"
        extra.write_text("extra content")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = ["skill", "my-skill"]
        args.vault = None
        args.here = False
        args.tools = None
        args.interactive = False
        args.main = False
        args.new_file = None

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)
            with mock.patch("sys.stdin") as mock_stdin:
                mock_stdin.isatty.return_value = False
                result = handle_edit(args)

        assert result == 0
        called_path = Path(mock_run.call_args[0][0][1])
        assert called_path == skill_file

    @mock.patch("artifactr.creator.get_default_vault")
    def test_main_flag_skips_picker(self, mock_default, tmp_path):
        """--main flag always opens SKILL.md without picker."""
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        (vault_dir / "skills" / "my-skill" / "extra.md").write_text("extra")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = ["skill", "my-skill"]
        args.vault = None
        args.here = False
        args.tools = None
        args.interactive = False
        args.main = True
        args.new_file = None

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)
            result = handle_edit(args)

        assert result == 0
        called_path = Path(mock_run.call_args[0][0][1])
        assert called_path == skill_file

    @mock.patch("artifactr.creator.get_default_vault")
    def test_single_file_skill_opens_directly(self, mock_default, tmp_path):
        """Skill with only SKILL.md should open directly, not show picker."""
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = ["skill", "my-skill"]
        args.vault = None
        args.here = False
        args.tools = None
        args.interactive = False
        args.main = False
        args.new_file = None

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)
            with mock.patch("sys.stdin") as mock_stdin:
                mock_stdin.isatty.return_value = True
                result = handle_edit(args)

        assert result == 0
        called_path = Path(mock_run.call_args[0][0][1])
        assert called_path == skill_file


# ---------------------------------------------------------------------------
# handle_list — artifact file listing
# ---------------------------------------------------------------------------


class TestHandleListArtifactName:
    @mock.patch("artifactr.cli.get_default_vault")
    def test_list_skill_files(self, mock_default, tmp_path, capsys):
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        ref_file = vault_dir / "skills" / "my-skill" / "refs" / "a.md"
        ref_file.parent.mkdir(parents=True)
        ref_file.write_text("ref content")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact_name = "my-skill"
        args.vaults = None

        result = handle_list(args)
        assert result == 0
        out = capsys.readouterr().out
        assert "SKILL.md" in out
        assert "(main)" in out
        assert "refs/a.md" in out

    @mock.patch("artifactr.cli.get_default_vault")
    def test_list_skill_files_type_prefix(self, mock_default, tmp_path, capsys):
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact_name = "sk/my-skill"
        args.vaults = None

        result = handle_list(args)
        assert result == 0
        out = capsys.readouterr().out
        assert "SKILL.md" in out

    @mock.patch("artifactr.cli.get_default_vault")
    def test_list_command_errors(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        cmd_file = vault_dir / "commands" / "my-cmd.md"
        cmd_file.parent.mkdir(parents=True)
        cmd_file.write_text("---\ndescription: test\n---\n")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact_name = "my-cmd"
        args.vaults = None

        result = handle_list(args)
        assert result == 1

    @mock.patch("artifactr.cli.get_default_vault")
    def test_list_not_found_errors(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        vault_dir.mkdir()
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact_name = "nonexistent"
        args.vaults = None

        result = handle_list(args)
        assert result == 1

    @mock.patch("artifactr.cli.get_default_vault")
    def test_list_single_file_skill(self, mock_default, tmp_path, capsys):
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact_name = "my-skill"
        args.vaults = None

        result = handle_list(args)
        assert result == 0
        out = capsys.readouterr().out
        assert "SKILL.md" in out
        assert "(main)" in out


# ---------------------------------------------------------------------------
# handle_cat
# ---------------------------------------------------------------------------


class TestHandleCat:
    @mock.patch("artifactr.cli.get_default_vault")
    def test_cat_skill(self, mock_default, tmp_path, capsys):
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\nContent here.")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = "my-skill"
        args.vault = None
        args.here = False
        args.tools = None

        with mock.patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = False
            result = handle_cat(args)

        assert result == 0
        out = capsys.readouterr().out
        assert "Content here." in out

    @mock.patch("artifactr.cli.get_default_vault")
    def test_cat_command(self, mock_default, tmp_path, capsys):
        vault_dir = tmp_path / "vault"
        cmd_file = vault_dir / "commands" / "my-cmd.md"
        cmd_file.parent.mkdir(parents=True)
        cmd_file.write_text("---\ndescription: test\n---\nCmd content.")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = "my-cmd"
        args.vault = None
        args.here = False
        args.tools = None

        result = handle_cat(args)
        assert result == 0
        out = capsys.readouterr().out
        assert "Cmd content." in out

    @mock.patch("artifactr.cli.get_default_vault")
    def test_cat_subpath(self, mock_default, tmp_path, capsys):
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        ref_file = vault_dir / "skills" / "my-skill" / "refs" / "hooks.md"
        ref_file.parent.mkdir(parents=True)
        ref_file.write_text("Hook content.")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = "my-skill/refs/hooks.md"
        args.vault = None
        args.here = False
        args.tools = None

        result = handle_cat(args)
        assert result == 0
        out = capsys.readouterr().out
        assert "Hook content." in out

    @mock.patch("artifactr.cli.get_default_vault")
    def test_cat_not_found(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        vault_dir.mkdir()
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = "nonexistent"
        args.vault = None
        args.here = False
        args.tools = None

        result = handle_cat(args)
        assert result == 1

    @mock.patch("artifactr.cli.get_default_vault")
    def test_cat_subpath_on_command_errors(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        cmd_file = vault_dir / "commands" / "my-cmd.md"
        cmd_file.parent.mkdir(parents=True)
        cmd_file.write_text("---\ndescription: test\n---\n")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = "c/my-cmd/some-file.md"
        args.vault = None
        args.here = False
        args.tools = None

        result = handle_cat(args)
        assert result == 1

    @mock.patch("artifactr.cli.get_default_vault")
    def test_cat_subpath_not_found(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = "my-skill/nonexistent.md"
        args.vault = None
        args.here = False
        args.tools = None

        result = handle_cat(args)
        assert result == 1

    @mock.patch("artifactr.cli.get_default_vault")
    def test_cat_frontmatter_name_fallback(self, mock_default, tmp_path, capsys):
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "folder-name" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: Display Name\n---\nContent here.")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = "Display Name"
        args.vault = None
        args.here = False
        args.tools = None

        result = handle_cat(args)
        assert result == 0
        out = capsys.readouterr().out
        assert "Content here." in out


# ---------------------------------------------------------------------------
# handle_inspect
# ---------------------------------------------------------------------------


class TestHandleInspect:
    @mock.patch("artifactr.cli.get_default_vault")
    def test_inspect_skill_frontmatter_and_files(self, mock_default, tmp_path, capsys):
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\ndescription: test desc\n---\n")
        ref_file = vault_dir / "skills" / "my-skill" / "refs" / "a.md"
        ref_file.parent.mkdir(parents=True)
        ref_file.write_text("ref content")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = "my-skill"
        args.vault = None
        args.here = False
        args.tools = None

        result = handle_inspect(args)
        assert result == 0
        out = capsys.readouterr().out
        assert "Frontmatter:" in out
        assert "name: my-skill" in out
        assert "description: test desc" in out
        assert "Files:" in out
        assert "SKILL.md" in out
        assert "(main)" in out

    @mock.patch("artifactr.cli.get_default_vault")
    def test_inspect_command_no_file_tree(self, mock_default, tmp_path, capsys):
        vault_dir = tmp_path / "vault"
        cmd_file = vault_dir / "commands" / "my-cmd.md"
        cmd_file.parent.mkdir(parents=True)
        cmd_file.write_text("---\ndescription: command desc\n---\n")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = "my-cmd"
        args.vault = None
        args.here = False
        args.tools = None

        result = handle_inspect(args)
        assert result == 0
        out = capsys.readouterr().out
        assert "Frontmatter:" in out
        assert "description: command desc" in out
        assert "Files:" not in out

    @mock.patch("artifactr.cli.get_default_vault")
    def test_inspect_no_frontmatter(self, mock_default, tmp_path, capsys):
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("No frontmatter here.")
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = "my-skill"
        args.vault = None
        args.here = False
        args.tools = None

        result = handle_inspect(args)
        assert result == 0
        out = capsys.readouterr().out
        assert "(no frontmatter found)" in out

    @mock.patch("artifactr.cli.get_default_vault")
    def test_inspect_not_found(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        vault_dir.mkdir()
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = "nonexistent"
        args.vault = None
        args.here = False
        args.tools = None

        result = handle_inspect(args)
        assert result == 1


# ---------------------------------------------------------------------------
# handle_export
# ---------------------------------------------------------------------------


class TestHandleExport:
    @mock.patch("artifactr.cli.get_default_vault")
    def test_export_skill(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\nContent.")
        ref_file = vault_dir / "skills" / "my-skill" / "refs" / "a.md"
        ref_file.parent.mkdir(parents=True)
        ref_file.write_text("ref content")
        mock_default.return_value = str(vault_dir)

        out_dir = tmp_path / "out"
        out_dir.mkdir()
        zip_path = out_dir / "my-skill.zip"

        args = mock.MagicMock()
        args.artifact = "my-skill"
        args.vault = None
        args.output = str(zip_path)

        result = handle_export(args)
        assert result == 0
        assert zip_path.exists()

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
        assert "my-skill/SKILL.md" in names
        assert "my-skill/refs/a.md" in names

    @mock.patch("artifactr.cli.get_default_vault")
    def test_export_command(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        cmd_file = vault_dir / "commands" / "my-cmd.md"
        cmd_file.parent.mkdir(parents=True)
        cmd_file.write_text("---\ndescription: test\n---\n")
        mock_default.return_value = str(vault_dir)

        out_dir = tmp_path / "out"
        out_dir.mkdir()
        zip_path = out_dir / "my-cmd.zip"

        args = mock.MagicMock()
        args.artifact = "my-cmd"
        args.vault = None
        args.output = str(zip_path)

        result = handle_export(args)
        assert result == 0

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
        assert "my-cmd/my-cmd.md" in names

    @mock.patch("artifactr.cli.get_default_vault")
    def test_export_output_collision(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        mock_default.return_value = str(vault_dir)

        existing_zip = tmp_path / "my-skill.zip"
        existing_zip.write_bytes(b"existing")

        args = mock.MagicMock()
        args.artifact = "my-skill"
        args.vault = None
        args.output = str(existing_zip)

        result = handle_export(args)
        assert result == 1

    @mock.patch("artifactr.cli.get_default_vault")
    def test_export_not_found(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        vault_dir.mkdir()
        mock_default.return_value = str(vault_dir)

        args = mock.MagicMock()
        args.artifact = "nonexistent"
        args.vault = None
        args.output = None

        result = handle_export(args)
        assert result == 1

    @mock.patch("artifactr.cli.get_default_vault")
    def test_export_no_manifest(self, mock_default, tmp_path):
        """Zip should contain no manifest.yaml."""
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")
        mock_default.return_value = str(vault_dir)

        out_dir = tmp_path / "out"
        out_dir.mkdir()
        zip_path = out_dir / "my-skill.zip"

        args = mock.MagicMock()
        args.artifact = "my-skill"
        args.vault = None
        args.output = str(zip_path)

        handle_export(args)

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
        assert "manifest.yaml" not in names


# ---------------------------------------------------------------------------
# _detect_zip_artifact_type
# ---------------------------------------------------------------------------


class TestDetectZipArtifactType:
    def test_single_skill(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("content")

        assert _detect_zip_artifact_type(tmp_path) == "single-skill"

    def test_single_file_artifact(self, tmp_path):
        art_dir = tmp_path / "my-cmd"
        art_dir.mkdir()
        (art_dir / "my-cmd.md").write_text("content")

        assert _detect_zip_artifact_type(tmp_path) == "single-file-artifact"

    def test_vault_bundle_multiple_dirs(self, tmp_path):
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir1" / "SKILL.md").write_text("content")
        (tmp_path / "dir2").mkdir()
        (tmp_path / "dir2" / "SKILL.md").write_text("content")

        assert _detect_zip_artifact_type(tmp_path) == "vault-bundle"

    def test_vault_bundle_with_skills_subdir(self, tmp_path):
        vault_dir = tmp_path / "my-vault"
        vault_dir.mkdir()
        (vault_dir / "skills").mkdir()
        (vault_dir / "skills" / "my-skill").mkdir()
        (vault_dir / "skills" / "my-skill" / "SKILL.md").write_text("content")

        assert _detect_zip_artifact_type(tmp_path) == "vault-bundle"

    def test_empty_raises(self, tmp_path):
        with pytest.raises(ValueError, match="no recognizable"):
            _detect_zip_artifact_type(tmp_path)

    def test_root_files_only_raises(self, tmp_path):
        (tmp_path / "README.md").write_text("not an artifact")
        with pytest.raises(ValueError, match="no recognizable"):
            _detect_zip_artifact_type(tmp_path)


# ---------------------------------------------------------------------------
# handle_store — zip input
# ---------------------------------------------------------------------------


class TestHandleStoreZip:
    @mock.patch("artifactr.cli.get_default_vault")
    def test_store_single_skill_zip(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        (vault_dir / "skills").mkdir(parents=True)
        mock_default.return_value = str(vault_dir)

        # Create a skill zip
        zip_path = tmp_path / "my-skill.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("my-skill/SKILL.md", "---\nname: my-skill\n---\n")

        args = mock.MagicMock()
        args.target_dir = str(zip_path)
        args.global_store = False
        args.vaults = None
        args.tools = None
        args.force = True
        args.skills = None
        args.commands = None
        args.agents = None

        result = handle_store(args)
        assert result == 0
        assert (vault_dir / "skills" / "my-skill" / "SKILL.md").exists()

    @mock.patch("artifactr.cli.get_default_vault")
    def test_store_zip_with_global_errors(self, mock_default, tmp_path):
        zip_path = tmp_path / "my-skill.zip"
        zip_path.write_bytes(b"fake")

        args = mock.MagicMock()
        args.target_dir = str(zip_path)
        args.global_store = True
        args.vaults = None

        result = handle_store(args)
        assert result == 1

    @mock.patch("artifactr.cli.get_default_vault")
    def test_store_nonexistent_zip_errors(self, mock_default, tmp_path):
        mock_default.return_value = str(tmp_path / "vault")

        args = mock.MagicMock()
        args.target_dir = str(tmp_path / "nonexistent.zip")
        args.global_store = False
        args.vaults = None

        result = handle_store(args)
        assert result == 1

    @mock.patch("artifactr.cli.get_default_vault")
    def test_store_invalid_zip_errors(self, mock_default, tmp_path):
        mock_default.return_value = str(tmp_path / "vault")
        bad_zip = tmp_path / "bad.zip"
        bad_zip.write_text("not a zip")

        args = mock.MagicMock()
        args.target_dir = str(bad_zip)
        args.global_store = False
        args.vaults = None

        result = handle_store(args)
        assert result == 1

    @mock.patch("artifactr.cli.get_default_vault")
    def test_store_empty_zip_errors(self, mock_default, tmp_path):
        vault_dir = tmp_path / "vault"
        vault_dir.mkdir()
        mock_default.return_value = str(vault_dir)

        zip_path = tmp_path / "empty.zip"
        with zipfile.ZipFile(zip_path, "w"):
            pass  # empty zip

        args = mock.MagicMock()
        args.target_dir = str(zip_path)
        args.global_store = False
        args.vaults = None
        args.force = True
        args.skills = None
        args.commands = None
        args.agents = None

        result = handle_store(args)
        assert result == 1


# ---------------------------------------------------------------------------
# Parser registration tests
# ---------------------------------------------------------------------------


class TestNewCommandParsers:
    def test_cat_parser_registered(self):
        parser = create_parser()
        args = parser.parse_args(["cat", "my-artifact"])
        assert args.command == "cat"
        assert args.artifact == "my-artifact"

    def test_cat_vault_flag(self):
        parser = create_parser()
        args = parser.parse_args(["cat", "my-artifact", "-V", "my-vault"])
        assert args.vault == "my-vault"

    def test_inspect_parser_registered(self):
        parser = create_parser()
        args = parser.parse_args(["inspect", "my-artifact"])
        assert args.command == "inspect"
        assert args.artifact == "my-artifact"

    def test_export_parser_registered(self):
        parser = create_parser()
        args = parser.parse_args(["export", "my-artifact"])
        assert args.command == "export"
        assert args.artifact == "my-artifact"

    def test_export_output_flag(self):
        parser = create_parser()
        args = parser.parse_args(["export", "my-artifact", "-o", "/tmp/out.zip"])
        assert args.output == "/tmp/out.zip"

    def test_ls_artifact_name_optional(self):
        parser = create_parser()
        args = parser.parse_args(["ls"])
        assert args.artifact_name is None

    def test_ls_with_artifact_name(self):
        parser = create_parser()
        args = parser.parse_args(["ls", "my-skill"])
        assert args.artifact_name == "my-skill"
