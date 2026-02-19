"""Tests for artifact editing (get_editor and resolve_edit_target)."""

import os
import platform
from pathlib import Path
from unittest import mock

import pytest

from artifactr.utils import get_editor
from artifactr.creator import resolve_edit_target


class TestGetEditor:
    """Tests for get_editor function."""

    def test_visual_env_var(self):
        """Verify $VISUAL is used when set."""
        with mock.patch.dict(os.environ, {"VISUAL": "code", "EDITOR": "nano"}):
            assert get_editor() == "code"

    def test_editor_env_var(self):
        """Verify $EDITOR is used when $VISUAL is not set."""
        with mock.patch.dict(os.environ, {"EDITOR": "emacs"}, clear=True):
            os.environ.pop("VISUAL", None)
            assert get_editor() == "emacs"

    @mock.patch("artifactr.utils.shutil.which")
    def test_fallback_nano(self, mock_which):
        """Verify nano is found in fallback chain."""
        mock_which.side_effect = lambda cmd: "/usr/bin/nano" if cmd == "nano" else None
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("VISUAL", None)
            os.environ.pop("EDITOR", None)
            assert get_editor() == "nano"

    @mock.patch("artifactr.utils.shutil.which")
    def test_fallback_nvim(self, mock_which):
        """Verify nvim is found when nano is not available."""
        def which_side_effect(cmd):
            if cmd == "nvim":
                return "/usr/bin/nvim"
            return None
        mock_which.side_effect = which_side_effect
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("VISUAL", None)
            os.environ.pop("EDITOR", None)
            assert get_editor() == "nvim"

    @mock.patch("artifactr.utils.shutil.which")
    def test_fallback_vim(self, mock_which):
        """Verify vim is found when nano and nvim are not available."""
        def which_side_effect(cmd):
            if cmd == "vim":
                return "/usr/bin/vim"
            return None
        mock_which.side_effect = which_side_effect
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("VISUAL", None)
            os.environ.pop("EDITOR", None)
            assert get_editor() == "vim"

    @mock.patch("artifactr.utils.platform.system", return_value="Linux")
    @mock.patch("artifactr.utils.shutil.which")
    def test_no_editor_found(self, mock_which, mock_platform):
        """Verify None is returned when no editor is available on non-Windows."""
        mock_which.return_value = None
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("VISUAL", None)
            os.environ.pop("EDITOR", None)
            assert get_editor() is None

    @mock.patch("artifactr.utils.platform.system", return_value="Windows")
    @mock.patch("artifactr.utils.shutil.which")
    def test_fallback_edit_windows(self, mock_which, mock_platform):
        """Verify edit is used before notepad.exe as a Windows fallback."""
        mock_which.side_effect = lambda cmd: "C:\\Windows\\edit.com" if cmd == "edit" else None
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("VISUAL", None)
            os.environ.pop("EDITOR", None)
            assert get_editor() == "edit"

    @mock.patch("artifactr.utils.platform.system", return_value="Windows")
    @mock.patch("artifactr.utils.shutil.which")
    def test_fallback_notepad_windows(self, mock_which, mock_platform):
        """Verify notepad.exe is used as last fallback on Windows when edit is not found."""
        mock_which.side_effect = lambda cmd: "C:\\Windows\\notepad.exe" if cmd == "notepad.exe" else None
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("VISUAL", None)
            os.environ.pop("EDITOR", None)
            assert get_editor() == "notepad.exe"

    @mock.patch("artifactr.utils.platform.system", return_value="Windows")
    @mock.patch("artifactr.utils.shutil.which")
    def test_no_editor_found_windows(self, mock_which, mock_platform):
        """Verify None is returned when no editor is found on Windows."""
        mock_which.return_value = None
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("VISUAL", None)
            os.environ.pop("EDITOR", None)
            assert get_editor() is None


class TestResolveEditTarget:
    """Tests for resolve_edit_target function."""

    @mock.patch("artifactr.creator.get_default_vault")
    def test_vault_mode_skill(self, mock_default, tmp_path):
        """Verify skill resolves to SKILL.md in vault."""
        vault_dir = tmp_path / "vault"
        skill_file = vault_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: my-skill\n---\n")

        mock_default.return_value = str(vault_dir)

        result = resolve_edit_target("skill", "my-skill")
        assert result["success"] is True
        assert result["path"] == skill_file

    @mock.patch("artifactr.creator.get_default_vault")
    def test_vault_mode_command(self, mock_default, tmp_path):
        """Verify command resolves to .md file in vault."""
        vault_dir = tmp_path / "vault"
        cmd_file = vault_dir / "commands" / "my-cmd.md"
        cmd_file.parent.mkdir(parents=True)
        cmd_file.write_text("---\ndescription: test\n---\n")

        mock_default.return_value = str(vault_dir)

        result = resolve_edit_target("command", "my-cmd")
        assert result["success"] is True
        assert result["path"] == cmd_file

    @mock.patch("artifactr.creator.get_default_vault")
    def test_vault_mode_not_found(self, mock_default, tmp_path):
        """Verify error when artifact doesn't exist in vault."""
        vault_dir = tmp_path / "vault"
        vault_dir.mkdir()

        mock_default.return_value = str(vault_dir)

        result = resolve_edit_target("skill", "nonexistent")
        assert result["success"] is False
        assert "not found" in result["error"]

    @mock.patch("artifactr.creator.get_default_tool")
    @mock.patch("artifactr.creator.get_tool")
    def test_here_mode(self, mock_get_tool, mock_default_tool, tmp_path, monkeypatch):
        """Verify --here resolves in current project."""
        monkeypatch.chdir(tmp_path)
        mock_default_tool.return_value = "claude-code"

        mock_adapter = mock.MagicMock()
        mock_adapter.supported_types = ["skills", "commands", "agents"]
        mock_adapter.get_destination.return_value = tmp_path / ".claude" / "skills"
        mock_get_tool.return_value = mock_adapter

        # Create the artifact
        skill_file = tmp_path / ".claude" / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("content")

        result = resolve_edit_target("skill", "my-skill", here=True)
        assert result["success"] is True
        assert result["path"] == skill_file

    @mock.patch("artifactr.creator.get_default_tool")
    @mock.patch("artifactr.creator.get_tool")
    def test_here_mode_not_found(self, mock_get_tool, mock_default_tool, tmp_path, monkeypatch):
        """Verify error when artifact not found in project."""
        monkeypatch.chdir(tmp_path)
        mock_default_tool.return_value = "claude-code"

        mock_adapter = mock.MagicMock()
        mock_adapter.supported_types = ["skills", "commands", "agents"]
        mock_adapter.get_destination.return_value = tmp_path / ".claude" / "skills"
        mock_get_tool.return_value = mock_adapter

        result = resolve_edit_target("skill", "nonexistent", here=True)
        assert result["success"] is False
        assert "not found" in result["error"]

    @mock.patch("artifactr.creator.get_default_vault")
    def test_no_default_vault(self, mock_default):
        """Verify error when no default vault is set."""
        mock_default.return_value = None

        result = resolve_edit_target("skill", "my-skill")
        assert result["success"] is False
        assert "No default vault" in result["error"]


class TestEditCLIParsing:
    """Tests for edit CLI argument parsing."""

    def test_edit_arguments_two_positional(self):
        """Verify edit accepts the old two-positional form (type name)."""
        from artifactr.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["edit", "skill", "my-skill"])
        assert args.command == "edit"
        assert args.artifact == ["skill", "my-skill"]

    def test_edit_arguments_unified(self):
        """Verify edit accepts the new unified specifier form."""
        from artifactr.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["edit", "my-skill"])
        assert args.command == "edit"
        assert args.artifact == ["my-skill"]

    def test_edit_specifier_with_type_prefix(self):
        """Verify edit accepts [type/]name specifier."""
        from artifactr.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["edit", "skill/my-skill"])
        assert args.artifact == ["skill/my-skill"]

    def test_edit_here_flag(self):
        """Verify --here flag is parsed."""
        from artifactr.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["edit", "command", "my-cmd", "-H"])
        assert args.here is True

    def test_edit_vault_flag(self):
        """Verify --vault flag is parsed."""
        from artifactr.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["edit", "agent", "my-agent", "--vault", "favs"])
        assert args.vault == "favs"

    def test_edit_interactive_flag(self):
        """Verify -i / --interactive flag is parsed."""
        from artifactr.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["edit", "my-skill", "-i"])
        assert args.interactive is True

    def test_edit_main_flag(self):
        """Verify -m / --main flag is parsed."""
        from artifactr.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["edit", "my-skill", "-m"])
        assert args.main is True

    def test_edit_new_file_flag(self):
        """Verify -n / --new-file flag is parsed."""
        from artifactr.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["edit", "my-skill", "-n", "refs/new.md"])
        assert args.new_file == "refs/new.md"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
