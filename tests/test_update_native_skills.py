"""Tests for art update-native-skills / art uns command."""

import argparse
from pathlib import Path
from unittest import mock

import pytest

from artifactr.cli import create_parser, handle_update_native_skills


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_args(**kwargs):
    defaults = {
        "global_install": False,
        "tools": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _mock_adapter(tmp_path, global_dest=None, local_dest=None, types=None):
    """Build a mock GenericToolAdapter."""
    if types is None:
        types = ["skills", "commands"]
    adapter = mock.MagicMock()
    adapter.supported_types = types
    adapter.get_global_destination.return_value = global_dest or (tmp_path / "global")
    adapter.get_destination.return_value = local_dest or (tmp_path / "local")
    return adapter


# ---------------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------------

def test_update_native_skills_registered():
    parser = create_parser()
    args = parser.parse_args(["update-native-skills"])
    assert args.command == "update-native-skills"


def test_uns_alias_registered():
    parser = create_parser()
    args = parser.parse_args(["uns"])
    assert args.command in ("update-native-skills", "uns")


def test_global_flag_registered():
    parser = create_parser()
    args = parser.parse_args(["update-native-skills", "-g"])
    assert args.global_install is True


def test_tools_flag_registered():
    parser = create_parser()
    args = parser.parse_args(["update-native-skills", "--tools", "claude-code"])
    assert args.tools == "claude-code"


# ---------------------------------------------------------------------------
# Local install (default, git repo)
# ---------------------------------------------------------------------------

def test_local_install_git_repo(tmp_path, capsys):
    """Local install in a git repo should succeed without prompting."""
    install_result = {"skills_installed": 4, "commands_installed": 3}
    args = _make_args()
    adapter = _mock_adapter(tmp_path, local_dest=tmp_path / "local")

    with mock.patch("artifactr.utils.is_git_repo", return_value=True), \
         mock.patch("artifactr.builtins.install_builtin_skills", return_value=install_result), \
         mock.patch("artifactr.cli.get_default_tool", return_value="claude-code"), \
         mock.patch("artifactr.cli.load_global_tools", return_value={}), \
         mock.patch("artifactr.cli.resolve_tool_name", return_value="claude-code"), \
         mock.patch("artifactr.cli.get_tool", return_value=adapter), \
         mock.patch("artifactr.cli.Path.cwd", return_value=tmp_path):
        rc = handle_update_native_skills(args)

    assert rc == 0
    out = capsys.readouterr().out
    assert "4 skill(s)" in out
    assert "3 command(s)" in out


# ---------------------------------------------------------------------------
# Git repo confirmation prompt
# ---------------------------------------------------------------------------

def test_local_install_not_git_repo_confirm_yes(tmp_path, capsys):
    """Local install outside git repo should prompt and succeed on Y."""
    install_result = {"skills_installed": 2, "commands_installed": 1}
    args = _make_args()
    adapter = _mock_adapter(tmp_path)

    with mock.patch("artifactr.utils.is_git_repo", return_value=False), \
         mock.patch("builtins.input", return_value="Y"), \
         mock.patch("artifactr.builtins.install_builtin_skills", return_value=install_result), \
         mock.patch("artifactr.cli.get_default_tool", return_value="claude-code"), \
         mock.patch("artifactr.cli.load_global_tools", return_value={}), \
         mock.patch("artifactr.cli.resolve_tool_name", return_value="claude-code"), \
         mock.patch("artifactr.cli.get_tool", return_value=adapter), \
         mock.patch("artifactr.cli.Path.cwd", return_value=tmp_path):
        rc = handle_update_native_skills(args)

    assert rc == 0


def test_local_install_not_git_repo_abort_on_n(tmp_path, capsys):
    """Local install outside git repo should abort on 'n'."""
    args = _make_args()

    with mock.patch("artifactr.utils.is_git_repo", return_value=False), \
         mock.patch("builtins.input", return_value="n"), \
         mock.patch("artifactr.cli.get_default_tool", return_value="claude-code"), \
         mock.patch("artifactr.cli.load_global_tools", return_value={}), \
         mock.patch("artifactr.cli.Path.cwd", return_value=tmp_path):
        rc = handle_update_native_skills(args)

    assert rc == 1
    out = capsys.readouterr().out
    assert "Aborted" in out


def test_no_prompt_inside_git_repo(tmp_path):
    """When CWD is a git repo, input() should not be called."""
    install_result = {"skills_installed": 4, "commands_installed": 3}
    args = _make_args()
    adapter = _mock_adapter(tmp_path)

    with mock.patch("artifactr.utils.is_git_repo", return_value=True), \
         mock.patch("builtins.input") as mock_input, \
         mock.patch("artifactr.builtins.install_builtin_skills", return_value=install_result), \
         mock.patch("artifactr.cli.get_default_tool", return_value="claude-code"), \
         mock.patch("artifactr.cli.load_global_tools", return_value={}), \
         mock.patch("artifactr.cli.resolve_tool_name", return_value="claude-code"), \
         mock.patch("artifactr.cli.get_tool", return_value=adapter), \
         mock.patch("artifactr.cli.Path.cwd", return_value=tmp_path):
        handle_update_native_skills(args)

    mock_input.assert_not_called()


# ---------------------------------------------------------------------------
# Global install
# ---------------------------------------------------------------------------

def test_global_install_skips_git_check(tmp_path, capsys):
    """Global install should not check for git repo."""
    install_result = {"skills_installed": 4, "commands_installed": 3}
    args = _make_args(global_install=True)
    adapter = _mock_adapter(tmp_path)

    with mock.patch("artifactr.utils.is_git_repo") as mock_git, \
         mock.patch("artifactr.builtins.install_builtin_skills", return_value=install_result), \
         mock.patch("artifactr.cli.get_default_tool", return_value="claude-code"), \
         mock.patch("artifactr.cli.load_global_tools", return_value={}), \
         mock.patch("artifactr.cli.resolve_tool_name", return_value="claude-code"), \
         mock.patch("artifactr.cli.get_tool", return_value=adapter):
        rc = handle_update_native_skills(args)

    mock_git.assert_not_called()
    assert rc == 0
    out = capsys.readouterr().out
    assert "globally" in out


def test_global_install_uses_global_dirs(tmp_path):
    """Global install should call get_global_destination, not get_destination."""
    install_result = {"skills_installed": 4, "commands_installed": 3}
    args = _make_args(global_install=True)
    adapter = _mock_adapter(tmp_path)

    with mock.patch("artifactr.builtins.install_builtin_skills", return_value=install_result), \
         mock.patch("artifactr.cli.get_default_tool", return_value="claude-code"), \
         mock.patch("artifactr.cli.load_global_tools", return_value={}), \
         mock.patch("artifactr.cli.resolve_tool_name", return_value="claude-code"), \
         mock.patch("artifactr.cli.get_tool", return_value=adapter):
        handle_update_native_skills(args)

    adapter.get_global_destination.assert_called()
    adapter.get_destination.assert_not_called()


# ---------------------------------------------------------------------------
# --tools override
# ---------------------------------------------------------------------------

def test_tools_override_single(tmp_path, capsys):
    """--tools claude-code should install only into claude-code dirs."""
    install_result = {"skills_installed": 4, "commands_installed": 3}
    args = _make_args(tools="claude-code", global_install=True)
    adapter = _mock_adapter(tmp_path)

    with mock.patch("artifactr.builtins.install_builtin_skills", return_value=install_result), \
         mock.patch("artifactr.cli.get_default_tool", return_value="opencode"), \
         mock.patch("artifactr.cli.load_global_tools", return_value={}), \
         mock.patch("artifactr.cli.resolve_tool_name", return_value="claude-code"), \
         mock.patch("artifactr.cli.get_tool", return_value=adapter):
        rc = handle_update_native_skills(args)

    assert rc == 0


def test_tools_override_unknown_tool(tmp_path, capsys):
    """Unknown tool should print error and return 1."""
    args = _make_args(tools="nonexistent-tool", global_install=True)

    with mock.patch("artifactr.cli.get_default_tool", return_value="opencode"), \
         mock.patch("artifactr.cli.load_global_tools", return_value={}), \
         mock.patch("artifactr.cli.resolve_tool_name", return_value="nonexistent-tool"), \
         mock.patch("artifactr.cli.get_tool", return_value=None):
        rc = handle_update_native_skills(args)

    assert rc == 1
    err = capsys.readouterr().err
    assert "Unknown tool" in err


# ---------------------------------------------------------------------------
# Silent overwrite
# ---------------------------------------------------------------------------

def test_silent_overwrite(tmp_path):
    """install_builtin_skills is called even when destination files exist."""
    install_result = {"skills_installed": 4, "commands_installed": 3}
    args = _make_args(global_install=True)
    adapter = _mock_adapter(tmp_path, global_dest=tmp_path)

    # Pre-create a destination file
    (tmp_path / "artifactr-context").mkdir()
    (tmp_path / "artifactr-context" / "artifact.md").write_text("old content")

    with mock.patch("artifactr.builtins.install_builtin_skills", return_value=install_result) as mock_install, \
         mock.patch("artifactr.cli.get_default_tool", return_value="claude-code"), \
         mock.patch("artifactr.cli.load_global_tools", return_value={}), \
         mock.patch("artifactr.cli.resolve_tool_name", return_value="claude-code"), \
         mock.patch("artifactr.cli.get_tool", return_value=adapter):
        rc = handle_update_native_skills(args)

    mock_install.assert_called_once()
    assert rc == 0
