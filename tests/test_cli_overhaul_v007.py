"""Comprehensive tests for CLI overhaul v0.0.7 changes.

Covers sections 10.1 through 10.14 of the task list:
- Type filter helpers (add_type_filter_args, resolve_type_filters)
- art list, art rm
- art proj import/rm/wipe/list
- art conf import/rm/wipe/list
- Enhanced spelunk
- art store with type filters
- Verification that old 'art import' command is removed
"""

import argparse
import sys
from pathlib import Path
from unittest import mock

import pytest

from artifactr.cli import (
    _apply_type_filters,
    _load_cache_entries,
    _load_global_cache_entries,
    add_type_filter_args,
    create_parser,
    handle_conf_import,
    handle_conf_list,
    handle_conf_rm,
    handle_conf_wipe,
    handle_list,
    handle_proj_import,
    handle_proj_list,
    handle_proj_rm,
    handle_proj_wipe,
    handle_rm,
    handle_spelunk,
    handle_store,
    main,
    resolve_type_filters,
)
from artifactr.importer import (
    remove_from_global_import_cache,
    remove_from_import_cache,
)
from artifactr.scanner import (
    discover_global_artifacts,
    discover_vault_artifacts,
    extract_description,
    is_vault,
    load_import_cache,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def make_vault(tmp_path):
    """Create a vault directory structure with test artifacts."""
    def _make(vault_dir=None):
        vault = vault_dir or (tmp_path / "vault")
        vault.mkdir(exist_ok=True)
        (vault / "vault.yaml").write_text("name: test-vault\n")

        skills = vault / "skills" / "my-skill"
        skills.mkdir(parents=True)
        (skills / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: A test skill\n---\nContent\n"
        )

        cmds = vault / "commands"
        cmds.mkdir(exist_ok=True)
        (cmds / "my-cmd.md").write_text(
            "---\nname: my-cmd\ndescription: A test command\n---\nContent\n"
        )

        agents = vault / "agents"
        agents.mkdir(exist_ok=True)
        (agents / "my-agent.md").write_text(
            "---\nname: my-agent\ndescription: A test agent\n---\nContent\n"
        )

        return vault

    return _make


@pytest.fixture
def make_project(tmp_path):
    """Create a project directory with .git and .art-cache structure."""
    def _make(cache_lines=None):
        proj = tmp_path / "project"
        proj.mkdir(exist_ok=True)
        (proj / ".git" / "info").mkdir(parents=True)
        (proj / ".git" / "info" / "exclude").write_text("")

        if cache_lines is not None:
            cache_dir = proj / ".art-cache"
            cache_dir.mkdir(exist_ok=True)
            (cache_dir / "imported").write_text(
                "\n".join(cache_lines) + "\n"
            )

        return proj

    return _make


# ---------------------------------------------------------------------------
# 10.1: Type filter helpers
# ---------------------------------------------------------------------------


class TestAddTypeFilterArgs:
    """Tests for add_type_filter_args."""

    def test_allow_names_true_adds_nargs_optional(self):
        parser = argparse.ArgumentParser()
        add_type_filter_args(parser, allow_names=True)

        # -S with a value
        ns = parser.parse_args(["-S", "foo,bar"])
        assert ns.skills == "foo,bar"

        # -S without a value -> const True
        ns = parser.parse_args(["-S"])
        assert ns.skills is True

        # No flag -> None
        ns = parser.parse_args([])
        assert ns.skills is None
        assert ns.commands is None
        assert ns.agents is None

    def test_allow_names_false_adds_store_true(self):
        parser = argparse.ArgumentParser()
        add_type_filter_args(parser, allow_names=False)

        ns = parser.parse_args(["-S"])
        assert ns.skills is True

        ns = parser.parse_args([])
        assert ns.skills is False

    def test_all_flags_present_names_mode(self):
        parser = argparse.ArgumentParser()
        add_type_filter_args(parser, allow_names=True)

        ns = parser.parse_args(["-S", "a,b", "-C", "-A", "x"])
        assert ns.skills == "a,b"
        assert ns.commands is True
        assert ns.agents == "x"

    def test_all_flags_present_boolean_mode(self):
        parser = argparse.ArgumentParser()
        add_type_filter_args(parser, allow_names=False)

        ns = parser.parse_args(["-S", "-C", "-A"])
        assert ns.skills is True
        assert ns.commands is True
        assert ns.agents is True

    def test_long_flag_names(self):
        parser = argparse.ArgumentParser()
        add_type_filter_args(parser, allow_names=True)

        ns = parser.parse_args(["--skills", "s1", "--commands", "--agents"])
        assert ns.skills == "s1"
        assert ns.commands is True
        assert ns.agents is True


class TestResolveTypeFilters:
    """Tests for resolve_type_filters."""

    def test_no_filters_returns_none(self):
        ns = argparse.Namespace(skills=None, commands=None, agents=None)
        assert resolve_type_filters(ns) is None

    def test_boolean_false_returns_none(self):
        ns = argparse.Namespace(skills=False, commands=False, agents=False)
        assert resolve_type_filters(ns) is None

    def test_flag_only_returns_true(self):
        ns = argparse.Namespace(skills=True, commands=None, agents=None)
        result = resolve_type_filters(ns)
        assert result == {"skills": True}

    def test_csv_names_returns_list(self):
        ns = argparse.Namespace(skills="a,b,c", commands=None, agents=None)
        result = resolve_type_filters(ns)
        assert result == {"skills": ["a", "b", "c"]}

    def test_mixed_filters(self):
        ns = argparse.Namespace(skills=True, commands="cmd1,cmd2", agents=None)
        result = resolve_type_filters(ns)
        assert result == {"skills": True, "commands": ["cmd1", "cmd2"]}

    def test_all_types_flag_only(self):
        ns = argparse.Namespace(skills=True, commands=True, agents=True)
        result = resolve_type_filters(ns)
        assert result == {"skills": True, "commands": True, "agents": True}

    def test_strips_whitespace_from_names(self):
        ns = argparse.Namespace(skills="a , b , c", commands=None, agents=None)
        result = resolve_type_filters(ns)
        assert result == {"skills": ["a", "b", "c"]}

    def test_missing_attributes_returns_none(self):
        ns = argparse.Namespace()
        assert resolve_type_filters(ns) is None


class TestApplyTypeFilters:
    """Tests for _apply_type_filters internal helper."""

    def test_filter_by_type_true(self):
        artifacts = [
            {"name": "s1", "type_plural": "skills"},
            {"name": "c1", "type_plural": "commands"},
            {"name": "a1", "type_plural": "agents"},
        ]
        result = _apply_type_filters(artifacts, {"skills": True})
        assert len(result) == 1
        assert result[0]["name"] == "s1"

    def test_filter_by_name_list(self):
        artifacts = [
            {"name": "s1", "type_plural": "skills"},
            {"name": "s2", "type_plural": "skills"},
            {"name": "c1", "type_plural": "commands"},
        ]
        result = _apply_type_filters(artifacts, {"skills": ["s1"]})
        assert len(result) == 1
        assert result[0]["name"] == "s1"

    def test_filter_multiple_types(self):
        artifacts = [
            {"name": "s1", "type_plural": "skills"},
            {"name": "c1", "type_plural": "commands"},
            {"name": "a1", "type_plural": "agents"},
        ]
        result = _apply_type_filters(
            artifacts, {"skills": True, "agents": True}
        )
        assert len(result) == 2
        names = {a["name"] for a in result}
        assert names == {"s1", "a1"}


# ---------------------------------------------------------------------------
# 10.2: art list command
# ---------------------------------------------------------------------------


class TestHandleList:
    """Tests for handle_list (vault-side listing)."""

    def test_list_artifacts(self, make_vault, capsys):
        vault = make_vault()
        args = argparse.Namespace(
            vaults=None, skills=None, commands=None, agents=None
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=str(vault)
        ):
            rc = handle_list(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "NAME" in out
        assert "TYPE" in out
        assert "DESCRIPTION" in out
        assert "my-skill" in out
        assert "my-cmd" in out
        assert "my-agent" in out

    def test_list_filter_skills_only(self, make_vault, capsys):
        vault = make_vault()
        args = argparse.Namespace(
            vault=None, skills=True, commands=None, agents=None
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=str(vault)
        ):
            rc = handle_list(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "my-skill" in out
        assert "my-cmd" not in out
        assert "my-agent" not in out

    def test_list_filter_by_name(self, make_vault, capsys):
        vault = make_vault()
        args = argparse.Namespace(
            vault=None, skills="my-skill", commands=None, agents=None
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=str(vault)
        ):
            rc = handle_list(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "my-skill" in out
        assert "my-cmd" not in out

    def test_list_empty_vault(self, tmp_path, capsys):
        vault = tmp_path / "empty-vault"
        vault.mkdir()
        (vault / "vault.yaml").write_text("name: empty\n")

        args = argparse.Namespace(
            vaults=None, skills=None, commands=None, agents=None
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=str(vault)
        ):
            rc = handle_list(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "No artifacts found" in out

    def test_list_no_default_vault(self, capsys):
        args = argparse.Namespace(
            vaults=None, skills=None, commands=None, agents=None
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=None
        ):
            rc = handle_list(args)

        assert rc == 1
        err = capsys.readouterr().err
        assert "No default vault set" in err

    def test_list_with_vault_arg(self, make_vault, capsys):
        vault = make_vault()
        args = argparse.Namespace(
            vaults=["myvault"], skills=None, commands=None, agents=None
        )
        with mock.patch(
            "artifactr.cli.get_vault_by_name_or_path",
            return_value=str(vault),
        ), mock.patch(
            "artifactr.cli.list_vaults",
            return_value={"vaults": [str(vault)], "default": str(vault), "vault_names": {str(vault): "myvault"}},
        ):
            rc = handle_list(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "my-skill" in out

    def test_list_vault_not_in_catalog(self, capsys):
        args = argparse.Namespace(
            vaults=["nonexistent"], skills=None, commands=None, agents=None
        )
        with mock.patch(
            "artifactr.cli.get_vault_by_name_or_path", return_value=None
        ):
            rc = handle_list(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "No artifacts found" in out


# ---------------------------------------------------------------------------
# 10.3: art rm command
# ---------------------------------------------------------------------------


class TestHandleRm:
    """Tests for handle_rm (vault-side removal)."""

    def test_rm_with_force(self, make_vault, capsys):
        vault = make_vault()
        args = argparse.Namespace(
            vault=None, names=["my-cmd"], force=True
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=str(vault)
        ):
            rc = handle_rm(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "Removed" in out
        assert not (vault / "commands" / "my-cmd.md").exists()

    def test_rm_skill_directory(self, make_vault, capsys):
        vault = make_vault()
        args = argparse.Namespace(
            vault=None, names=["skills/my-skill"], force=True
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=str(vault)
        ):
            rc = handle_rm(args)

        assert rc == 0
        assert not (vault / "skills" / "my-skill").exists()

    def test_rm_with_type_prefix(self, make_vault, capsys):
        vault = make_vault()
        args = argparse.Namespace(
            vault=None, names=["commands/my-cmd"], force=True
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=str(vault)
        ):
            rc = handle_rm(args)

        assert rc == 0
        assert not (vault / "commands" / "my-cmd.md").exists()

    def test_rm_nonexistent_artifact(self, make_vault, capsys):
        vault = make_vault()
        args = argparse.Namespace(
            vault=None, names=["nonexistent"], force=True
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=str(vault)
        ):
            rc = handle_rm(args)

        assert rc == 1
        err = capsys.readouterr().err
        assert "No matching" in err or "not found" in err.lower()

    def test_rm_aborts_without_force(self, make_vault, capsys):
        vault = make_vault()
        args = argparse.Namespace(
            vault=None, names=["my-cmd"], force=False
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=str(vault)
        ), mock.patch("builtins.input", side_effect=EOFError):
            rc = handle_rm(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "Aborted" in out
        # File should still exist
        assert (vault / "commands" / "my-cmd.md").exists()

    def test_rm_confirms_with_yes(self, make_vault, capsys):
        vault = make_vault()
        args = argparse.Namespace(
            vault=None, names=["my-cmd"], force=False
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=str(vault)
        ), mock.patch("builtins.input", return_value="y"):
            rc = handle_rm(args)

        assert rc == 0
        assert not (vault / "commands" / "my-cmd.md").exists()

    def test_rm_no_default_vault(self, capsys):
        args = argparse.Namespace(
            vault=None, names=["something"], force=True
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=None
        ):
            rc = handle_rm(args)

        assert rc == 1
        err = capsys.readouterr().err
        assert "No default vault set" in err


# ---------------------------------------------------------------------------
# 10.4: art proj import
# ---------------------------------------------------------------------------


class TestHandleProjImport:
    """Tests for handle_proj_import."""

    def test_uses_cwd_as_default_target(self, make_vault, make_project):
        vault = make_vault()
        proj = make_project()
        args = argparse.Namespace(
            target=None,
            vault=None,
            tools="claude-code",
            artifacts=None,
            link=False,
            force=True,
            no_exclude=False,
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=str(vault)
        ), mock.patch(
            "artifactr.cli.get_default_tool", return_value="claude-code"
        ), mock.patch(
            "artifactr.cli._load_vault_tools_for_import"
        ), mock.patch(
            "artifactr.cli.import_artifacts",
            return_value={
                "success": True,
                "errors": [],
                "imported": {"claude-code": {"skills": 1}},
                "skipped": 0,
            },
        ) as mock_import, mock.patch(
            "artifactr.tools.reload_registry"
        ), mock.patch(
            "pathlib.Path.cwd", return_value=proj
        ):
            rc = handle_proj_import(args)

        assert rc == 0
        call_kwargs = mock_import.call_args
        assert call_kwargs[1]["target"] == str(proj) or call_kwargs.kwargs.get("target") == str(proj)

    def test_no_exclude_flag(self, make_vault, make_project):
        vault = make_vault()
        proj = make_project()
        args = argparse.Namespace(
            target=str(proj),
            vault=None,
            tools="claude-code",
            artifacts=None,
            link=False,
            force=True,
            no_exclude=True,
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli._load_vault_tools_for_import"
        ), mock.patch(
            "artifactr.cli.get_default_tool", return_value="claude-code"
        ), mock.patch(
            "artifactr.cli.import_artifacts",
            return_value={
                "success": True,
                "errors": [],
                "imported": {},
                "skipped": 0,
            },
        ) as mock_import, mock.patch(
            "artifactr.tools.reload_registry"
        ):
            handle_proj_import(args)

        _, kwargs = mock_import.call_args
        assert kwargs["no_exclude"] is True

    def test_type_filters_passed_through(self, make_vault, make_project):
        vault = make_vault()
        proj = make_project()
        args = argparse.Namespace(
            target=str(proj),
            vault=None,
            tools="claude-code",
            artifacts=None,
            link=False,
            force=True,
            no_exclude=False,
            skills=True,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli._load_vault_tools_for_import"
        ), mock.patch(
            "artifactr.cli.get_default_tool", return_value="claude-code"
        ), mock.patch(
            "artifactr.cli.import_artifacts",
            return_value={
                "success": True,
                "errors": [],
                "imported": {},
                "skipped": 0,
            },
        ) as mock_import, mock.patch(
            "artifactr.tools.reload_registry"
        ):
            handle_proj_import(args)

        _, kwargs = mock_import.call_args
        assert kwargs["type_filters"] == {"skills": True}

    def test_import_failure_returns_1(self, make_project, capsys):
        proj = make_project()
        args = argparse.Namespace(
            target=str(proj),
            vault=None,
            tools="claude-code",
            artifacts=None,
            link=False,
            force=True,
            no_exclude=False,
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli._load_vault_tools_for_import"
        ), mock.patch(
            "artifactr.cli.get_default_tool", return_value="claude-code"
        ), mock.patch(
            "artifactr.cli.import_artifacts",
            return_value={
                "success": False,
                "errors": ["Error: Something failed"],
                "imported": {},
                "skipped": 0,
            },
        ), mock.patch(
            "artifactr.tools.reload_registry"
        ):
            rc = handle_proj_import(args)

        assert rc == 1
        err = capsys.readouterr().err
        assert "Something failed" in err


# ---------------------------------------------------------------------------
# 10.5: art proj rm
# ---------------------------------------------------------------------------


class TestHandleProjRm:
    """Tests for handle_proj_rm."""

    def test_no_cache_returns_error(self, tmp_path, capsys):
        proj = tmp_path / "proj"
        proj.mkdir()
        args = argparse.Namespace(
            target=str(proj),
            names=["something"],
            tools=None,
            force=True,
            skills=False,
            commands=False,
            agents=False,
        )
        with mock.patch(
            "artifactr.cli.load_global_tools", return_value={}
        ), mock.patch(
            "artifactr.cli.load_active_vault_tools", return_value=({}, None)
        ):
            rc = handle_proj_rm(args)

        assert rc == 1
        err = capsys.readouterr().err
        assert "No imported artifacts" in err

    def test_removes_matching_artifact(self, make_project, tmp_path, capsys):
        proj = make_project(cache_lines=["test-vault.claude-code.my-cmd"])

        # Create the artifact file in the project
        cmd_dir = proj / ".claude" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "my-cmd.md").write_text("---\nname: my-cmd\n---\n")

        tool_config_dirs = {
            "claude-code": {
                "skills": ".claude/skills",
                "commands": ".claude/commands",
                "agents": ".claude/agents",
            }
        }

        args = argparse.Namespace(
            target=str(proj),
            names=["my-cmd"],
            tools=None,
            force=True,
            skills=False,
            commands=False,
            agents=False,
        )
        with mock.patch(
            "artifactr.cli.load_global_tools", return_value={}
        ), mock.patch(
            "artifactr.cli.load_active_vault_tools", return_value=({}, None)
        ), mock.patch(
            "artifactr.cli.get_tool_config_dirs", return_value=tool_config_dirs
        ):
            rc = handle_proj_rm(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "Removed" in out
        assert not (cmd_dir / "my-cmd.md").exists()


# ---------------------------------------------------------------------------
# 10.6: art proj wipe
# ---------------------------------------------------------------------------


class TestHandleProjWipe:
    """Tests for handle_proj_wipe."""

    def test_no_cache_returns_0(self, tmp_path, capsys):
        proj = tmp_path / "proj"
        proj.mkdir()
        args = argparse.Namespace(
            target=str(proj),
            tools=None,
            force=True,
            skills=None,
            commands=None,
            agents=None,
        )
        rc = handle_proj_wipe(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "No imported artifacts" in out

    def test_wipe_with_force_removes_all(self, make_project, capsys):
        proj = make_project(cache_lines=["test-vault.claude-code.my-cmd"])

        cmd_dir = proj / ".claude" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "my-cmd.md").write_text("---\nname: my-cmd\n---\n")

        tool_config_dirs = {
            "claude-code": {
                "commands": ".claude/commands",
            }
        }

        args = argparse.Namespace(
            target=str(proj),
            tools=None,
            force=True,
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli.load_global_tools", return_value={}
        ), mock.patch(
            "artifactr.cli.load_active_vault_tools", return_value=({}, None)
        ), mock.patch(
            "artifactr.cli.get_tool_config_dirs", return_value=tool_config_dirs
        ):
            rc = handle_proj_wipe(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "Removed" in out
        assert not (cmd_dir / "my-cmd.md").exists()

    def test_wipe_aborts_on_eof(self, make_project, capsys):
        proj = make_project(cache_lines=["test-vault.claude-code.my-cmd"])

        cmd_dir = proj / ".claude" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "my-cmd.md").write_text("---\nname: my-cmd\n---\n")

        tool_config_dirs = {
            "claude-code": {
                "commands": ".claude/commands",
            }
        }

        args = argparse.Namespace(
            target=str(proj),
            tools=None,
            force=False,
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli.load_global_tools", return_value={}
        ), mock.patch(
            "artifactr.cli.load_active_vault_tools", return_value=({}, None)
        ), mock.patch(
            "artifactr.cli.get_tool_config_dirs", return_value=tool_config_dirs
        ), mock.patch("builtins.input", side_effect=EOFError):
            rc = handle_proj_wipe(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "Aborted" in out
        # File should still exist
        assert (cmd_dir / "my-cmd.md").exists()

    def test_wipe_with_type_filter(self, make_project, capsys):
        proj = make_project(
            cache_lines=[
                "test-vault.claude-code.my-cmd",
                "test-vault.claude-code.my-skill",
            ]
        )

        cmd_dir = proj / ".claude" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "my-cmd.md").write_text("content\n")

        skill_dir = proj / ".claude" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("content\n")

        tool_config_dirs = {
            "claude-code": {
                "skills": ".claude/skills",
                "commands": ".claude/commands",
            }
        }

        args = argparse.Namespace(
            target=str(proj),
            tools=None,
            force=True,
            skills=None,
            commands=True,  # Only wipe commands
            agents=None,
        )
        with mock.patch(
            "artifactr.cli.load_global_tools", return_value={}
        ), mock.patch(
            "artifactr.cli.load_active_vault_tools", return_value=({}, None)
        ), mock.patch(
            "artifactr.cli.get_tool_config_dirs", return_value=tool_config_dirs
        ):
            rc = handle_proj_wipe(args)

        assert rc == 0
        # Command should be removed, skill should remain
        assert not (cmd_dir / "my-cmd.md").exists()
        assert (skill_dir / "SKILL.md").exists()


# ---------------------------------------------------------------------------
# 10.7: art proj list
# ---------------------------------------------------------------------------


class TestHandleProjList:
    """Tests for handle_proj_list."""

    def test_list_imported_artifacts(self, make_project, capsys):
        proj = make_project(
            cache_lines=[
                "test-vault.claude-code.my-skill",
                "test-vault.claude-code.my-cmd",
            ]
        )
        args = argparse.Namespace(
            target=str(proj),
            tools=None,
            skills=None,
            commands=None,
            agents=None,
        )
        rc = handle_proj_list(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "NAME" in out
        assert "TOOL" in out
        assert "my-skill" in out
        assert "my-cmd" in out

    def test_list_no_cache(self, tmp_path, capsys):
        proj = tmp_path / "proj"
        proj.mkdir()
        args = argparse.Namespace(
            target=str(proj),
            tools=None,
            skills=None,
            commands=None,
            agents=None,
        )
        rc = handle_proj_list(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "No imported artifacts" in out

    def test_list_with_tool_filter(self, make_project, capsys):
        proj = make_project(
            cache_lines=[
                "test-vault.claude-code.my-skill",
                "test-vault.opencode.other-skill",
            ]
        )
        args = argparse.Namespace(
            target=str(proj),
            tools="claude-code",
            skills=None,
            commands=None,
            agents=None,
        )
        rc = handle_proj_list(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "my-skill" in out
        assert "other-skill" not in out

    def test_list_uses_cwd_as_default(self, make_project, capsys):
        proj = make_project(
            cache_lines=["test-vault.claude-code.my-skill"]
        )
        args = argparse.Namespace(
            target=None,
            tools=None,
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch("pathlib.Path.cwd", return_value=proj):
            rc = handle_proj_list(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "my-skill" in out


# ---------------------------------------------------------------------------
# 10.8: art conf import
# ---------------------------------------------------------------------------


class TestHandleConfImport:
    """Tests for handle_conf_import."""

    def test_conf_import_calls_import_artifacts_global(self, capsys):
        args = argparse.Namespace(
            vault=None,
            tools="claude-code",
            artifacts=None,
            link=False,
            force=True,
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli._load_vault_tools_for_import"
        ), mock.patch(
            "artifactr.cli.get_default_tool", return_value="claude-code"
        ), mock.patch(
            "artifactr.cli.import_artifacts_global",
            return_value={
                "success": True,
                "errors": [],
                "imported": {"claude-code": {"skills": 2}},
                "skipped": 0,
            },
        ) as mock_import, mock.patch(
            "artifactr.tools.reload_registry"
        ):
            rc = handle_conf_import(args)

        assert rc == 0
        mock_import.assert_called_once()

    def test_conf_import_passes_type_filters(self):
        args = argparse.Namespace(
            vault=None,
            tools="claude-code",
            artifacts=None,
            link=False,
            force=True,
            skills=True,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli._load_vault_tools_for_import"
        ), mock.patch(
            "artifactr.cli.get_default_tool", return_value="claude-code"
        ), mock.patch(
            "artifactr.cli.import_artifacts_global",
            return_value={
                "success": True,
                "errors": [],
                "imported": {},
                "skipped": 0,
            },
        ) as mock_import, mock.patch(
            "artifactr.tools.reload_registry"
        ):
            handle_conf_import(args)

        _, kwargs = mock_import.call_args
        assert kwargs["type_filters"] == {"skills": True}

    def test_conf_import_failure(self, capsys):
        args = argparse.Namespace(
            vault=None,
            tools="claude-code",
            artifacts=None,
            link=False,
            force=True,
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli._load_vault_tools_for_import"
        ), mock.patch(
            "artifactr.cli.get_default_tool", return_value="claude-code"
        ), mock.patch(
            "artifactr.cli.import_artifacts_global",
            return_value={
                "success": False,
                "errors": ["Error: No default vault"],
                "imported": {},
                "skipped": 0,
            },
        ), mock.patch(
            "artifactr.tools.reload_registry"
        ):
            rc = handle_conf_import(args)

        assert rc == 1


# ---------------------------------------------------------------------------
# 10.9-10.11: art conf rm, wipe, list
# ---------------------------------------------------------------------------


class TestHandleConfRm:
    """Tests for handle_conf_rm."""

    def test_no_global_cache(self, capsys):
        args = argparse.Namespace(
            names=["something"],
            tools=None,
            force=True,
            skills=False,
            commands=False,
            agents=False,
        )
        with mock.patch(
            "artifactr.cli._load_global_cache_entries", return_value=[]
        ):
            rc = handle_conf_rm(args)

        assert rc == 1
        err = capsys.readouterr().err
        assert "No globally imported" in err

    def test_rm_no_matching(self, capsys):
        cache = [
            {
                "name": "other",
                "tool": "claude-code",
                "vault": "v",
                "type": "unknown",
                "type_plural": "unknown",
                "raw": "v.claude-code.other",
            }
        ]
        args = argparse.Namespace(
            names=["nonexistent"],
            tools=None,
            force=True,
            skills=False,
            commands=False,
            agents=False,
        )
        with mock.patch(
            "artifactr.cli._load_global_cache_entries", return_value=cache
        ), mock.patch(
            "artifactr.cli.load_global_tools", return_value={}
        ), mock.patch(
            "artifactr.cli.load_active_vault_tools", return_value=({}, None)
        ), mock.patch(
            "artifactr.cli.get_tool_global_dirs", return_value={}
        ):
            rc = handle_conf_rm(args)

        assert rc == 1
        err = capsys.readouterr().err
        assert "No matching" in err


class TestHandleConfWipe:
    """Tests for handle_conf_wipe."""

    def test_no_global_cache(self, capsys):
        args = argparse.Namespace(
            tools=None,
            force=True,
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli._load_global_cache_entries", return_value=[]
        ):
            rc = handle_conf_wipe(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "No globally imported" in out

    def test_wipe_aborts_on_decline(self, tmp_path, capsys):
        cache = [
            {
                "name": "my-cmd",
                "tool": "claude-code",
                "vault": "v",
                "type": "unknown",
                "type_plural": "unknown",
                "raw": "v.claude-code.my-cmd",
            }
        ]
        global_dir = tmp_path / "global-commands"
        global_dir.mkdir()
        (global_dir / "my-cmd.md").write_text("content\n")

        tool_global_dirs = {
            "claude-code": {"commands": str(global_dir)}
        }

        args = argparse.Namespace(
            tools=None,
            force=False,
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli._load_global_cache_entries", return_value=cache
        ), mock.patch(
            "artifactr.cli.load_global_tools", return_value={}
        ), mock.patch(
            "artifactr.cli.load_active_vault_tools", return_value=({}, None)
        ), mock.patch(
            "artifactr.cli.get_tool_global_dirs", return_value=tool_global_dirs
        ), mock.patch("builtins.input", return_value="n"):
            rc = handle_conf_wipe(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "Aborted" in out
        assert (global_dir / "my-cmd.md").exists()


class TestHandleConfList:
    """Tests for handle_conf_list."""

    def test_list_no_global_cache(self, capsys):
        args = argparse.Namespace(
            tools=None,
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli._load_global_cache_entries", return_value=[]
        ):
            rc = handle_conf_list(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "No globally imported" in out

    def test_list_shows_entries(self, capsys):
        cache = [
            {
                "name": "my-skill",
                "tool": "claude-code",
                "vault": "test-vault",
                "type": "skill",
                "type_plural": "skills",
                "raw": "test-vault.claude-code.my-skill",
            }
        ]
        args = argparse.Namespace(
            tools=None,
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli._load_global_cache_entries", return_value=cache
        ):
            rc = handle_conf_list(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "NAME" in out
        assert "my-skill" in out

    def test_list_with_tool_filter(self, capsys):
        cache = [
            {
                "name": "s1",
                "tool": "claude-code",
                "vault": "v",
                "type": "skill",
                "type_plural": "skills",
                "raw": "v.claude-code.s1",
            },
            {
                "name": "s2",
                "tool": "opencode",
                "vault": "v",
                "type": "skill",
                "type_plural": "skills",
                "raw": "v.opencode.s2",
            },
        ]
        args = argparse.Namespace(
            tools="claude-code",
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli._load_global_cache_entries", return_value=cache
        ):
            rc = handle_conf_list(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "s1" in out
        assert "s2" not in out

    def test_list_with_type_filter(self, capsys):
        cache = [
            {
                "name": "s1",
                "tool": "claude-code",
                "vault": "v",
                "type": "skill",
                "type_plural": "skills",
                "raw": "v.claude-code.s1",
            },
            {
                "name": "c1",
                "tool": "claude-code",
                "vault": "v",
                "type": "command",
                "type_plural": "commands",
                "raw": "v.claude-code.c1",
            },
        ]
        args = argparse.Namespace(
            tools=None,
            skills=True,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli._load_global_cache_entries", return_value=cache
        ):
            rc = handle_conf_list(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "s1" in out
        assert "c1" not in out


# ---------------------------------------------------------------------------
# 10.12: Enhanced spelunk
# ---------------------------------------------------------------------------


class TestHandleSpelunk:
    """Tests for handle_spelunk."""

    def test_no_target_defaults_to_cwd(self, tmp_path, capsys):
        """With no target and no --global flag, spelunk defaults to CWD (not global config)."""
        args = argparse.Namespace(
            target=None,
            global_spelunk=False,
            tools=None,
            skills=None,
            commands=None,
            agents=None,
            verbose=False,
            depth=2,
            format="human",
        )
        with mock.patch("pathlib.Path.cwd", return_value=tmp_path), \
             mock.patch("artifactr.cli.discover_global_artifacts") as mock_global, \
             mock.patch("artifactr.cli.is_vault", return_value=False), \
             mock.patch("artifactr.cli.discover_artifacts", return_value=[]), \
             mock.patch("artifactr.cli.discover_artifacts_by_structure", return_value=[]), \
             mock.patch("artifactr.cli.load_import_cache", return_value={}):
            rc = handle_spelunk(args)

        assert rc == 0
        mock_global.assert_not_called()
        out = capsys.readouterr().out
        assert "global config" not in out.lower()

    def test_explicit_global_flag(self, capsys):
        args = argparse.Namespace(
            target=None,
            global_spelunk=True,
            tools=None,
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli.discover_global_artifacts", return_value=[]
        ) as mock_discover:
            rc = handle_spelunk(args)

        assert rc == 0
        mock_discover.assert_called_once()

    def test_vault_directory_detected(self, make_vault, capsys):
        vault = make_vault()
        args = argparse.Namespace(
            target=str(vault),
            global_spelunk=False,
            tools=None,
            skills=None,
            commands=None,
            agents=None,
        )
        rc = handle_spelunk(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "my-skill" in out
        assert "my-cmd" in out
        assert "my-agent" in out

    def test_type_filter_on_vault_spelunk(self, make_vault, capsys):
        vault = make_vault()
        args = argparse.Namespace(
            target=str(vault),
            global_spelunk=False,
            tools=None,
            skills=True,
            commands=None,
            agents=None,
        )
        rc = handle_spelunk(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "my-skill" in out
        assert "my-cmd" not in out
        assert "my-agent" not in out

    def test_nonexistent_target(self, tmp_path, capsys):
        args = argparse.Namespace(
            target=str(tmp_path / "nonexistent"),
            global_spelunk=False,
            tools=None,
            skills=None,
            commands=None,
            agents=None,
        )
        rc = handle_spelunk(args)

        assert rc == 1
        err = capsys.readouterr().err
        assert "does not exist" in err

    def test_tools_filter(self, make_vault, capsys):
        vault = make_vault()
        args = argparse.Namespace(
            target=str(vault),
            global_spelunk=False,
            tools="claude-code",
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli.load_global_tools", return_value={}
        ), mock.patch(
            "artifactr.cli.load_active_vault_tools", return_value=({}, None)
        ):
            rc = handle_spelunk(args)

        assert rc == 0
        # Vault spelunk doesn't really filter by tool, but it should still succeed
        out = capsys.readouterr().out
        assert "my-skill" in out

    def test_no_artifacts_found(self, tmp_path, capsys):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        args = argparse.Namespace(
            target=str(empty_dir),
            global_spelunk=False,
            tools=None,
            skills=None,
            commands=None,
            agents=None,
        )
        rc = handle_spelunk(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "No artifacts found" in out

    def test_location_column_present_no_tool_column(self, make_vault, capsys):
        """LOCATION column shown; TOOL column absent in human format."""
        vault = make_vault()
        args = argparse.Namespace(
            target=str(vault),
            global_spelunk=False,
            tools=None,
            skills=None,
            commands=None,
            agents=None,
            verbose=False,
            depth=2,
            format="human",
        )
        rc = handle_spelunk(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "LOCATION" in out
        assert "TOOL" not in out
        assert "DESCRIPTION" not in out

    def test_verbose_flag_adds_description(self, make_vault, capsys):
        """--verbose re-enables the DESCRIPTION column."""
        vault = make_vault()
        args = argparse.Namespace(
            target=str(vault),
            global_spelunk=False,
            tools=None,
            skills=None,
            commands=None,
            agents=None,
            verbose=True,
            depth=2,
            format="human",
        )
        rc = handle_spelunk(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "DESCRIPTION" in out
        assert "LOCATION" in out

    def test_location_is_relative_to_vault_root(self, make_vault, capsys):
        """LOCATION column is relative to the vault root, not absolute."""
        vault = make_vault()
        args = argparse.Namespace(
            target=str(vault),
            global_spelunk=False,
            tools=None,
            skills=None,
            commands=None,
            agents=None,
            verbose=False,
            depth=2,
            format="human",
        )
        rc = handle_spelunk(args)

        assert rc == 0
        out = capsys.readouterr().out
        # Path should be relative (not absolute), so no leading '/'
        for line in out.splitlines()[1:]:  # skip header
            if line.strip():
                cols = [c.strip() for c in line.split("  ") if c.strip()]
                # location col should be a relative path like "skills/my-skill"
                if len(cols) >= 3:
                    loc = cols[2]
                    assert not loc.startswith("/"), f"Expected relative path, got: {loc}"

    def test_markdown_format_has_location_column(self, make_vault, capsys):
        """Markdown format output uses Location column, not Source/Path."""
        vault = make_vault()
        args = argparse.Namespace(
            target=str(vault),
            global_spelunk=False,
            tools=None,
            skills=None,
            commands=None,
            agents=None,
            verbose=False,
            depth=2,
            format="md",
        )
        rc = handle_spelunk(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "Location" in out
        assert "Source" not in out
        assert "Path" not in out

    def test_no_target_spelunks_cwd_artifacts(self, tmp_path, capsys):
        """art spelunk with no args discovers artifacts in CWD."""
        skill_dir = tmp_path / "skills" / "my-cwd-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: my-cwd-skill\ndescription: A skill\n---\n")

        args = argparse.Namespace(
            target=None,
            global_spelunk=False,
            tools=None,
            skills=None,
            commands=None,
            agents=None,
            verbose=False,
            depth=2,
            format="human",
        )
        with mock.patch("pathlib.Path.cwd", return_value=tmp_path), \
             mock.patch("artifactr.cli.load_import_cache", return_value={}):
            rc = handle_spelunk(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "my-cwd-skill" in out


# ---------------------------------------------------------------------------
# 10.13: art store with type filters
# ---------------------------------------------------------------------------


class TestHandleStore:
    """Tests for handle_store."""

    def test_store_nonexistent_target(self, capsys):
        args = argparse.Namespace(
            target_dir="/nonexistent/path",
            vault=None,
            skills=None,
            commands=None,
            agents=None,
        )
        rc = handle_store(args)

        assert rc == 1
        err = capsys.readouterr().err
        assert "does not exist" in err

    def test_store_no_default_vault(self, tmp_path, capsys):
        target = tmp_path / "source"
        target.mkdir()

        args = argparse.Namespace(
            target_dir=str(target),
            vault=None,
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=None
        ):
            rc = handle_store(args)

        assert rc == 1
        err = capsys.readouterr().err
        assert "No default vault set" in err

    def test_store_no_artifacts_found(self, tmp_path, capsys):
        target = tmp_path / "source"
        target.mkdir()
        vault = tmp_path / "vault"
        vault.mkdir()

        args = argparse.Namespace(
            target_dir=str(target),
            vault=None,
            skills=None,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=str(vault)
        ), mock.patch(
            "artifactr.cli.list_vaults",
            return_value={"vaults": [str(vault)], "default": str(vault), "vault_names": {}},
        ), mock.patch(
            "artifactr.cli.discover_artifacts", return_value=[]
        ):
            rc = handle_store(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "No artifacts found" in out

    def test_store_type_filter_applied(self, tmp_path, capsys):
        target = tmp_path / "source"
        target.mkdir()
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "skills").mkdir()

        all_artifacts = [
            {"name": "s1", "type": "skill", "type_plural": "skills", "path": target / "s1"},
            {"name": "c1", "type": "command", "type_plural": "commands", "path": target / "c1.md"},
        ]

        args = argparse.Namespace(
            target_dir=str(target),
            vault=None,
            skills=True,
            commands=None,
            agents=None,
        )
        with mock.patch(
            "artifactr.cli.get_default_vault", return_value=str(vault)
        ), mock.patch(
            "artifactr.cli.list_vaults",
            return_value={"vaults": [str(vault)], "default": str(vault), "vault_names": {}},
        ), mock.patch(
            "artifactr.cli.discover_artifacts", return_value=all_artifacts
        ), mock.patch("builtins.input", side_effect=EOFError):
            rc = handle_store(args)

        assert rc == 0
        out = capsys.readouterr().out
        # With -S filter, only the skill should be listed
        assert "s1" in out
        assert "c1" not in out


# ---------------------------------------------------------------------------
# 10.14: Verify old 'art import' is removed
# ---------------------------------------------------------------------------


class TestOldImportRemoved:
    """Verify that 'import' is not a top-level subcommand."""

    def test_import_not_a_top_level_command(self):
        parser = create_parser()
        # argparse should raise SystemExit for an unrecognized command
        with pytest.raises(SystemExit):
            parser.parse_args(["import", "/some/path"])

    def test_proj_import_is_valid(self):
        parser = create_parser()
        # proj import should parse fine
        ns = parser.parse_args(["proj", "import", "/some/path"])
        assert ns.command == "proj"
        assert ns.proj_command == "import"
        assert ns.target == "/some/path"

    def test_conf_import_is_valid(self):
        parser = create_parser()
        ns = parser.parse_args(["conf", "import"])
        assert ns.command == "conf"
        assert ns.conf_command == "import"


# ---------------------------------------------------------------------------
# Parser integration tests
# ---------------------------------------------------------------------------


class TestCreateParser:
    """Tests for create_parser verifying all new subcommands exist."""

    def test_ls_command(self):
        parser = create_parser()
        ns = parser.parse_args(["ls"])
        assert ns.command == "ls"

    def test_ls_with_type_flags(self):
        parser = create_parser()
        ns = parser.parse_args(["ls", "-S", "foo,bar", "-C"])
        assert ns.skills == "foo,bar"
        assert ns.commands is True

    def test_rm_command(self):
        parser = create_parser()
        ns = parser.parse_args(["rm", "my-artifact", "--force"])
        assert ns.command == "rm"
        assert ns.names == ["my-artifact"]
        assert ns.force is True

    def test_rm_multiple_names(self):
        parser = create_parser()
        ns = parser.parse_args(["rm", "a1", "a2", "skills/a3"])
        assert ns.names == ["a1", "a2", "skills/a3"]

    def test_proj_import_defaults(self):
        parser = create_parser()
        ns = parser.parse_args(["proj", "import"])
        assert ns.command == "proj"
        assert ns.proj_command == "import"
        assert ns.target is None
        assert ns.no_exclude is False

    def test_proj_import_with_flags(self):
        parser = create_parser()
        ns = parser.parse_args([
            "proj", "import", "/my/project",
            "--vault", "myvault",
            "--tools", "claude-code",
            "--no-exclude",
            "-S",
            "--force",
        ])
        assert ns.target == "/my/project"
        assert ns.vaults == ["myvault"]
        assert ns.tools == "claude-code"
        assert ns.no_exclude is True
        assert ns.skills is True
        assert ns.force is True

    def test_proj_rm_command(self):
        parser = create_parser()
        ns = parser.parse_args(["proj", "rm", "my-art", "--force"])
        assert ns.proj_command == "rm"
        assert ns.names == ["my-art"]
        assert ns.force is True

    def test_proj_rm_store_true_type_flags(self):
        parser = create_parser()
        ns = parser.parse_args(["proj", "rm", "x", "-S", "-C"])
        # allow_names=False so these are store_true
        assert ns.skills is True
        assert ns.commands is True
        assert ns.agents is False

    def test_proj_wipe_command(self):
        parser = create_parser()
        ns = parser.parse_args(["proj", "wipe", "--force", "--tools", "claude"])
        assert ns.proj_command == "wipe"
        assert ns.force is True
        assert ns.tools == "claude"

    def test_proj_ls_command(self):
        parser = create_parser()
        ns = parser.parse_args(["proj", "ls", "--tools", "opencode"])
        assert ns.proj_command == "ls"
        assert ns.tools == "opencode"

    def test_conf_import_command(self):
        parser = create_parser()
        ns = parser.parse_args(["conf", "import", "--vault", "v", "-S"])
        assert ns.command == "conf"
        assert ns.conf_command == "import"
        assert ns.vaults == ["v"]
        assert ns.skills is True

    def test_conf_rm_command(self):
        parser = create_parser()
        ns = parser.parse_args(["conf", "rm", "art1", "--force"])
        assert ns.conf_command == "rm"
        assert ns.names == ["art1"]
        assert ns.force is True

    def test_conf_wipe_command(self):
        parser = create_parser()
        ns = parser.parse_args(["conf", "wipe", "--force"])
        assert ns.conf_command == "wipe"
        assert ns.force is True

    def test_conf_ls_command(self):
        parser = create_parser()
        ns = parser.parse_args(["conf", "ls", "--tools", "claude-code"])
        assert ns.conf_command == "ls"
        assert ns.tools == "claude-code"

    def test_spelunk_no_target(self):
        parser = create_parser()
        ns = parser.parse_args(["spelunk"])
        assert ns.command == "spelunk"
        assert ns.target is None

    def test_spelunk_with_target_and_flags(self):
        parser = create_parser()
        ns = parser.parse_args([
            "spelunk", "/some/dir", "--tools", "claude-code", "-S", "-A"
        ])
        assert ns.target == "/some/dir"
        assert ns.tools == "claude-code"
        assert ns.skills is True
        assert ns.agents is True

    def test_spelunk_global_flag(self):
        parser = create_parser()
        ns = parser.parse_args(["spelunk", "--global"])
        assert ns.global_spelunk is True

    def test_store_command_with_type_filters(self):
        parser = create_parser()
        ns = parser.parse_args(["store", "/dir", "-S", "my-skill", "-C"])
        assert ns.command == "store"
        assert ns.target_dir == "/dir"
        assert ns.skills == "my-skill"
        assert ns.commands is True

    def test_project_alias(self):
        parser = create_parser()
        ns = parser.parse_args(["project", "ls"])
        assert ns.command == "project"
        assert ns.proj_command == "ls"

    def test_config_alias(self):
        parser = create_parser()
        ns = parser.parse_args(["config", "ls"])
        assert ns.command == "config"
        assert ns.conf_command == "ls"


# ---------------------------------------------------------------------------
# Scanner unit tests
# ---------------------------------------------------------------------------


class TestIsVault:
    """Tests for scanner.is_vault."""

    def test_directory_with_vault_yaml(self, tmp_path):
        (tmp_path / "vault.yaml").write_text("name: test\n")
        assert is_vault(tmp_path) is True

    def test_directory_without_vault_yaml(self, tmp_path):
        assert is_vault(tmp_path) is False


class TestDiscoverVaultArtifacts:
    """Tests for scanner.discover_vault_artifacts."""

    def test_discovers_all_types(self, make_vault):
        vault = make_vault()
        artifacts = discover_vault_artifacts(vault)

        names = {a["name"] for a in artifacts}
        assert "my-skill" in names
        assert "my-cmd" in names
        assert "my-agent" in names

    def test_correct_types(self, make_vault):
        vault = make_vault()
        artifacts = discover_vault_artifacts(vault)

        by_name = {a["name"]: a for a in artifacts}
        assert by_name["my-skill"]["type"] == "skill"
        assert by_name["my-skill"]["type_plural"] == "skills"
        assert by_name["my-cmd"]["type"] == "command"
        assert by_name["my-cmd"]["type_plural"] == "commands"
        assert by_name["my-agent"]["type"] == "agent"
        assert by_name["my-agent"]["type_plural"] == "agents"

    def test_empty_vault(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "vault.yaml").write_text("name: empty\n")
        artifacts = discover_vault_artifacts(vault)
        assert artifacts == []

    def test_sorted_output(self, make_vault):
        vault = make_vault()
        artifacts = discover_vault_artifacts(vault)
        # Should be sorted by type then name
        types = [a["type"] for a in artifacts]
        assert types == sorted(types)


class TestExtractDescription:
    """Tests for scanner.extract_description."""

    def test_extracts_from_skill(self, make_vault):
        vault = make_vault()
        artifacts = discover_vault_artifacts(vault)
        skill = next(a for a in artifacts if a["name"] == "my-skill")
        desc = extract_description(skill)
        assert desc == "A test skill"

    def test_extracts_from_command(self, make_vault):
        vault = make_vault()
        artifacts = discover_vault_artifacts(vault)
        cmd = next(a for a in artifacts if a["name"] == "my-cmd")
        desc = extract_description(cmd)
        assert desc == "A test command"

    def test_no_frontmatter(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("No frontmatter here")
        art = {"name": "test", "type": "command", "path": f}
        assert extract_description(art) == "-"

    def test_truncates_long_description(self, tmp_path):
        long_desc = "A" * 60
        f = tmp_path / "test.md"
        f.write_text(f"---\ndescription: {long_desc}\n---\n")
        art = {"name": "test", "type": "command", "path": f}
        desc = extract_description(art)
        assert desc.endswith("...")
        assert len(desc) == 53  # 50 chars + "..."


# ---------------------------------------------------------------------------
# Import cache helpers
# ---------------------------------------------------------------------------


class TestLoadCacheEntries:
    """Tests for _load_cache_entries."""

    def test_loads_entries(self, tmp_path):
        cache_dir = tmp_path / ".art-cache"
        cache_dir.mkdir()
        (cache_dir / "imported").write_text(
            "vault1.claude-code.skill1\nvault1.opencode.cmd1\n"
        )
        entries = _load_cache_entries(tmp_path)
        assert len(entries) == 2
        assert entries[0]["name"] == "skill1"
        assert entries[0]["tool"] == "claude-code"
        assert entries[0]["vault"] == "vault1"
        assert entries[1]["name"] == "cmd1"
        assert entries[1]["tool"] == "opencode"

    def test_no_cache_file(self, tmp_path):
        entries = _load_cache_entries(tmp_path)
        assert entries == []

    def test_skips_malformed_lines(self, tmp_path):
        cache_dir = tmp_path / ".art-cache"
        cache_dir.mkdir()
        (cache_dir / "imported").write_text("bad\nok.tool.name\n\n")
        entries = _load_cache_entries(tmp_path)
        assert len(entries) == 1
        assert entries[0]["name"] == "name"


class TestRemoveFromImportCache:
    """Tests for importer.remove_from_import_cache."""

    def test_removes_specified_names(self, tmp_path):
        cache_dir = tmp_path / ".art-cache"
        cache_dir.mkdir()
        cache_file = cache_dir / "imported"
        cache_file.write_text(
            "v.tool.keep\nv.tool.remove\nv.tool.also-keep\n"
        )

        remove_from_import_cache(tmp_path, ["remove"])

        content = cache_file.read_text()
        assert "keep" in content
        assert "also-keep" in content
        assert "remove" not in content

    def test_no_cache_file_no_error(self, tmp_path):
        # Should not raise
        remove_from_import_cache(tmp_path, ["anything"])


class TestRemoveFromGlobalImportCache:
    """Tests for importer.remove_from_global_import_cache."""

    def test_removes_from_global_cache(self, tmp_path):
        cache_dir = tmp_path / ".config" / "artifactr" / ".art-cache-global"
        cache_dir.mkdir(parents=True)
        cache_file = cache_dir / "imported"
        cache_file.write_text("v.tool.keep\nv.tool.remove\n")

        with mock.patch("pathlib.Path.home", return_value=tmp_path):
            remove_from_global_import_cache(["remove"])

        content = cache_file.read_text()
        assert "keep" in content
        assert "remove" not in content

    def test_no_global_cache_file(self, tmp_path):
        with mock.patch("pathlib.Path.home", return_value=tmp_path):
            # Should not raise
            remove_from_global_import_cache(["anything"])


class TestLoadImportCache:
    """Tests for scanner.load_import_cache."""

    def test_loads_cache(self, tmp_path):
        cache_dir = tmp_path / ".art-cache"
        cache_dir.mkdir()
        (cache_dir / "imported").write_text(
            "vault1.claude-code.skill1\nvault2.claude-code.skill1\n"
        )
        result = load_import_cache(tmp_path)
        assert "skill1" in result
        assert "vault1" in result["skill1"]
        assert "vault2" in result["skill1"]

    def test_no_cache_returns_empty(self, tmp_path):
        result = load_import_cache(tmp_path)
        assert result == {}


# ---------------------------------------------------------------------------
# Main dispatch tests
# ---------------------------------------------------------------------------


class TestMainDispatch:
    """Tests for main() routing to correct handlers."""

    def test_main_ls_dispatch(self):
        with mock.patch(
            "sys.argv", ["art", "ls"]
        ), mock.patch(
            "artifactr.cli.handle_list", return_value=0
        ) as mock_handler:
            rc = main()
        assert rc == 0
        mock_handler.assert_called_once()

    def test_main_rm_dispatch(self):
        with mock.patch(
            "sys.argv", ["art", "rm", "foo", "--force"]
        ), mock.patch(
            "artifactr.cli.handle_rm", return_value=0
        ) as mock_handler:
            rc = main()
        assert rc == 0
        mock_handler.assert_called_once()

    def test_main_proj_import_dispatch(self):
        with mock.patch(
            "sys.argv", ["art", "proj", "import"]
        ), mock.patch(
            "artifactr.cli.handle_proj_import", return_value=0
        ) as mock_handler:
            rc = main()
        assert rc == 0
        mock_handler.assert_called_once()

    def test_main_proj_rm_dispatch(self):
        with mock.patch(
            "sys.argv", ["art", "proj", "rm", "x"]
        ), mock.patch(
            "artifactr.cli.handle_proj_rm", return_value=0
        ) as mock_handler:
            rc = main()
        assert rc == 0
        mock_handler.assert_called_once()

    def test_main_proj_wipe_dispatch(self):
        with mock.patch(
            "sys.argv", ["art", "proj", "wipe", "--force"]
        ), mock.patch(
            "artifactr.cli.handle_proj_wipe", return_value=0
        ) as mock_handler:
            rc = main()
        assert rc == 0
        mock_handler.assert_called_once()

    def test_main_proj_ls_dispatch(self):
        with mock.patch(
            "sys.argv", ["art", "proj", "ls"]
        ), mock.patch(
            "artifactr.cli.handle_proj_list", return_value=0
        ) as mock_handler:
            rc = main()
        assert rc == 0
        mock_handler.assert_called_once()

    def test_main_conf_import_dispatch(self):
        with mock.patch(
            "sys.argv", ["art", "conf", "import"]
        ), mock.patch(
            "artifactr.cli.handle_conf_import", return_value=0
        ) as mock_handler:
            rc = main()
        assert rc == 0
        mock_handler.assert_called_once()

    def test_main_conf_rm_dispatch(self):
        with mock.patch(
            "sys.argv", ["art", "conf", "rm", "x"]
        ), mock.patch(
            "artifactr.cli.handle_conf_rm", return_value=0
        ) as mock_handler:
            rc = main()
        assert rc == 0
        mock_handler.assert_called_once()

    def test_main_conf_wipe_dispatch(self):
        with mock.patch(
            "sys.argv", ["art", "conf", "wipe"]
        ), mock.patch(
            "artifactr.cli.handle_conf_wipe", return_value=0
        ) as mock_handler:
            rc = main()
        assert rc == 0
        mock_handler.assert_called_once()

    def test_main_conf_ls_dispatch(self):
        with mock.patch(
            "sys.argv", ["art", "conf", "ls"]
        ), mock.patch(
            "artifactr.cli.handle_conf_list", return_value=0
        ) as mock_handler:
            rc = main()
        assert rc == 0
        mock_handler.assert_called_once()

    def test_main_spelunk_dispatch(self):
        with mock.patch(
            "sys.argv", ["art", "spelunk"]
        ), mock.patch(
            "artifactr.cli.handle_spelunk", return_value=0
        ) as mock_handler:
            rc = main()
        assert rc == 0
        mock_handler.assert_called_once()

    def test_main_store_dispatch(self):
        with mock.patch(
            "sys.argv", ["art", "store", "/dir"]
        ), mock.patch(
            "artifactr.cli.handle_store", return_value=0
        ) as mock_handler:
            rc = main()
        assert rc == 0
        mock_handler.assert_called_once()

    def test_main_no_command_prints_help(self, capsys):
        with mock.patch("sys.argv", ["art"]):
            rc = main()
        assert rc == 0


# ---------------------------------------------------------------------------
# Alias comma-separation tests
# ---------------------------------------------------------------------------


class TestToolAddAliasParsing:
    """Tests for comma-separated alias flattening in art tool add."""

    def test_comma_separated_aliases(self, tmp_path):
        """--alias a,b should produce aliases: ['a', 'b']."""
        from artifactr.cli import handle_tool_add

        args = argparse.Namespace(
            name="my-tool",
            skills=".t/skills",
            commands=None,
            agents=None,
            global_skills=None,
            global_commands=None,
            global_agents=None,
            aliases=["mt,mytool"],
            vaults=None,
            global_config=False,
        )
        with mock.patch("artifactr.cli.load_global_tools", return_value={}), \
             mock.patch("artifactr.cli.save_global_tools") as mock_save:
            handle_tool_add(args)

        saved = mock_save.call_args[0][0]
        assert saved["my-tool"]["aliases"] == ["mt", "mytool"]

    def test_repeatable_aliases(self, tmp_path):
        """--alias a --alias b should produce aliases: ['a', 'b']."""
        from artifactr.cli import handle_tool_add

        args = argparse.Namespace(
            name="my-tool",
            skills=".t/skills",
            commands=None,
            agents=None,
            global_skills=None,
            global_commands=None,
            global_agents=None,
            aliases=["mt", "mytool"],
            vaults=None,
            global_config=False,
        )
        with mock.patch("artifactr.cli.load_global_tools", return_value={}), \
             mock.patch("artifactr.cli.save_global_tools") as mock_save:
            handle_tool_add(args)

        saved = mock_save.call_args[0][0]
        assert saved["my-tool"]["aliases"] == ["mt", "mytool"]

    def test_mixed_alias_styles(self, tmp_path):
        """--alias mt,mytool --alias m should produce aliases: ['mt', 'mytool', 'm']."""
        from artifactr.cli import handle_tool_add

        args = argparse.Namespace(
            name="my-tool",
            skills=".t/skills",
            commands=None,
            agents=None,
            global_skills=None,
            global_commands=None,
            global_agents=None,
            aliases=["mt,mytool", "m"],
            vaults=None,
            global_config=False,
        )
        with mock.patch("artifactr.cli.load_global_tools", return_value={}), \
             mock.patch("artifactr.cli.save_global_tools") as mock_save:
            handle_tool_add(args)

        saved = mock_save.call_args[0][0]
        assert saved["my-tool"]["aliases"] == ["mt", "mytool", "m"]


# ---------------------------------------------------------------------------
# Config edit command tests
# ---------------------------------------------------------------------------


class TestConfigEdit:
    """Tests for art config edit command."""

    def test_config_edit_parser_registration(self):
        parser = create_parser()
        ns = parser.parse_args(["config", "edit"])
        assert ns.command == "config"
        assert ns.conf_command == "edit"

    def test_config_edit_via_conf_alias(self):
        parser = create_parser()
        ns = parser.parse_args(["conf", "edit"])
        assert ns.conf_command == "edit"

    def test_config_edit_opens_editor(self, tmp_path):
        from artifactr.cli import handle_config_edit

        args = argparse.Namespace()
        config_dir = tmp_path / "config"

        with mock.patch("artifactr.utils.get_editor", return_value="nano"), \
             mock.patch("artifactr.utils.get_config_dir", return_value=config_dir), \
             mock.patch("subprocess.run", return_value=mock.Mock(returncode=0)) as mock_run:
            rc = handle_config_edit(args)

        assert rc == 0
        mock_run.assert_called_once_with(["nano", str(config_dir / "config.yaml")])
        assert config_dir.is_dir()

    def test_config_edit_no_editor(self, capsys):
        from artifactr.cli import handle_config_edit

        args = argparse.Namespace()

        with mock.patch("artifactr.utils.get_editor", return_value=None):
            rc = handle_config_edit(args)

        assert rc == 1
        assert "No editor found" in capsys.readouterr().err

    def test_config_edit_dispatch(self):
        with mock.patch(
            "sys.argv", ["art", "config", "edit"]
        ), mock.patch(
            "artifactr.cli.handle_config_edit", return_value=0
        ) as mock_handler:
            rc = main()
        assert rc == 0
        mock_handler.assert_called_once()


# ---------------------------------------------------------------------------
# CLI QoL Updates: create slash syntax + -V flag
# ---------------------------------------------------------------------------


class TestCreateSlashSyntax:
    """Tests for art create type/name slash syntax."""

    def test_create_skill_slash(self):
        from artifactr.cli import _main
        with mock.patch("sys.argv", ["art", "create", "skill/my-skill"]), \
             mock.patch("artifactr.cli.handle_create_skill", return_value=0) as mock_create:
            rc = _main()
        assert rc == 0
        mock_create.assert_called_once()
        ns = mock_create.call_args[0][0]
        assert ns.create_command == "skill"
        assert ns.skill_name == "my-skill"

    def test_create_cmd_slash(self):
        from artifactr.cli import _main
        with mock.patch("sys.argv", ["art", "create", "cmd/my-cmd"]), \
             mock.patch("artifactr.cli.handle_create_artifact", return_value=0) as mock_create:
            rc = _main()
        assert rc == 0
        mock_create.assert_called_once()
        ns, artifact_type = mock_create.call_args[0]
        assert ns.create_command == "cmd"
        assert ns.command_name == "my-cmd"
        assert artifact_type == "command"

    def test_create_agt_slash(self):
        from artifactr.cli import _main
        with mock.patch("sys.argv", ["art", "create", "agt/my-agent"]), \
             mock.patch("artifactr.cli.handle_create_artifact", return_value=0) as mock_create:
            rc = _main()
        assert rc == 0
        mock_create.assert_called_once()
        ns, artifact_type = mock_create.call_args[0]
        assert ns.create_command == "agt"
        assert ns.agent_name == "my-agent"
        assert artifact_type == "agent"

    def test_create_cr_alias_slash(self):
        """cr alias also works with slash syntax."""
        from artifactr.cli import _main
        with mock.patch("sys.argv", ["art", "cr", "skill/test-skill"]), \
             mock.patch("artifactr.cli.handle_create_skill", return_value=0) as mock_create:
            rc = _main()
        assert rc == 0
        ns = mock_create.call_args[0][0]
        assert ns.create_command == "skill"
        assert ns.skill_name == "test-skill"

    def test_create_invalid_slash_type_falls_through(self):
        """Unknown type before slash does not pre-process and lets argparse error."""
        from artifactr.cli import _main
        with mock.patch("sys.argv", ["art", "create", "unknown/name"]):
            with pytest.raises(SystemExit):
                _main()


class TestVersionFlag:
    """Test for art -V short version flag."""

    def test_version_short_flag(self, capsys):
        from artifactr.cli import create_parser
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["-V"])
        assert exc_info.value.code == 0
