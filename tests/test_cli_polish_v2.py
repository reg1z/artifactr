"""Tests for CLI polish v2 changes.

Covers:
- Command aliases (sp, st, cr, ed, edit s/c/a)
- Store --force flag
- Orphaned import detection
- KeyboardInterrupt handling
"""

import argparse
import sys
from pathlib import Path
from unittest import mock

import pytest

from artifactr.cli import (
    check_import_health,
    create_parser,
    handle_store,
    handle_spelunk,
    main,
)


# ---------------------------------------------------------------------------
# 6.1 Command alias tests
# ---------------------------------------------------------------------------


class TestCommandAliases:
    """Tests for new command aliases."""

    def test_spelunk_sp_alias(self):
        parser = create_parser()
        ns = parser.parse_args(["sp"])
        assert ns.command in ("spelunk", "sp")

    def test_store_st_alias(self):
        parser = create_parser()
        ns = parser.parse_args(["st", "/tmp"])
        assert ns.command in ("store", "st")

    def test_create_cr_alias(self):
        parser = create_parser()
        ns = parser.parse_args(["cr", "skill", "test-skill", "-d", "desc"])
        assert ns.command in ("create", "cr")
        assert ns.create_command == "skill"

    def test_edit_ed_alias(self):
        parser = create_parser()
        ns = parser.parse_args(["ed", "skill", "test-skill"])
        assert ns.command in ("edit", "ed")

    def test_config_edit_ed_alias(self):
        parser = create_parser()
        ns = parser.parse_args(["config", "ed"])
        assert ns.command in ("config", "conf", "c")
        assert ns.conf_command in ("edit", "ed")

    def test_config_conf_ed_alias(self):
        parser = create_parser()
        ns = parser.parse_args(["conf", "ed"])
        assert ns.command in ("config", "conf", "c")
        assert ns.conf_command in ("edit", "ed")

    def test_edit_type_alias_s(self):
        parser = create_parser()
        ns = parser.parse_args(["edit", "s", "my-skill"])
        assert ns.artifact_type == "s"

    def test_edit_type_alias_c(self):
        parser = create_parser()
        ns = parser.parse_args(["edit", "c", "my-cmd"])
        assert ns.artifact_type == "c"

    def test_edit_type_alias_a(self):
        parser = create_parser()
        ns = parser.parse_args(["edit", "a", "my-agent"])
        assert ns.artifact_type == "a"


# ---------------------------------------------------------------------------
# 6.2 Store --force tests
# ---------------------------------------------------------------------------


class TestStoreForce:
    """Tests for art store --force flag."""

    def test_force_flag_parsed(self):
        parser = create_parser()
        ns = parser.parse_args(["store", "/tmp", "--force"])
        assert ns.force is True

    def test_force_flag_short(self):
        parser = create_parser()
        ns = parser.parse_args(["store", "/tmp", "-f"])
        assert ns.force is True

    def test_no_force_default(self):
        parser = create_parser()
        ns = parser.parse_args(["store", "/tmp"])
        assert ns.force is False

    def test_force_passes_through_to_copy(self, tmp_path):
        """When --force is set, copy_with_prompt should receive force=True."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        vault_dir = tmp_path / "vault"
        vault_dir.mkdir()
        (vault_dir / "vault.yaml").write_text("name: test-vault\n")

        fake_artifacts = [
            {
                "name": "test-skill",
                "type": "skill",
                "type_plural": "skills",
                "path": source_dir / "skills" / "test-skill",
            }
        ]

        parser = create_parser()
        ns = parser.parse_args(["store", str(source_dir), "-f"])

        with mock.patch("artifactr.cli.get_default_vault", return_value=str(vault_dir)), \
             mock.patch("artifactr.cli.list_vaults", return_value={
                 "vaults": [str(vault_dir)],
                 "default": str(vault_dir),
                 "vault_names": {str(vault_dir): "test-vault"},
             }), \
             mock.patch("artifactr.cli.discover_artifacts", return_value=fake_artifacts), \
             mock.patch("artifactr.cli.copy_with_prompt", return_value={"copied": 1}) as mock_copy, \
             mock.patch("builtins.input", return_value="all"):
            handle_store(ns)
            assert mock_copy.call_count == 1
            _, kwargs = mock_copy.call_args
            assert kwargs.get("force") is True


# ---------------------------------------------------------------------------
# 6.3 Orphaned import detection tests
# ---------------------------------------------------------------------------


class TestOrphanedImportDetection:
    """Tests for check_import_health."""

    def test_healthy_import(self, tmp_path):
        """Source exists — returns None."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "vault.yaml").write_text("name: test-vault\n")
        skills = vault / "skills" / "my-skill"
        skills.mkdir(parents=True)
        (skills / "SKILL.md").write_text("---\nname: my-skill\n---\n")

        with mock.patch(
            "artifactr.cli.get_vault_by_name_or_path",
            return_value=str(vault),
        ):
            result = check_import_health("my-skill", "skill", "test-vault")
            assert result is None

    def test_source_missing(self, tmp_path):
        """Vault exists but artifact is gone — returns 'source missing'."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "vault.yaml").write_text("name: test-vault\n")
        (vault / "skills").mkdir()

        with mock.patch(
            "artifactr.cli.get_vault_by_name_or_path",
            return_value=str(vault),
        ):
            result = check_import_health("my-skill", "skill", "test-vault")
            assert result == "source missing"

    def test_vault_not_found_unregistered(self):
        """Vault name not in catalog — returns 'vault not found'."""
        with mock.patch(
            "artifactr.cli.get_vault_by_name_or_path",
            return_value=None,
        ):
            result = check_import_health("my-skill", "skill", "old-vault")
            assert result == "vault not found"

    def test_vault_not_found_path_gone(self, tmp_path):
        """Vault registered but path doesn't exist — returns 'vault not found'."""
        gone_path = tmp_path / "gone-vault"
        with mock.patch(
            "artifactr.cli.get_vault_by_name_or_path",
            return_value=str(gone_path),
        ):
            result = check_import_health("my-skill", "skill", "old-vault")
            assert result == "vault not found"

    def test_command_source_missing(self, tmp_path):
        """Command type uses .md file check."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "vault.yaml").write_text("name: test-vault\n")
        (vault / "commands").mkdir()

        with mock.patch(
            "artifactr.cli.get_vault_by_name_or_path",
            return_value=str(vault),
        ):
            result = check_import_health("my-cmd", "command", "test-vault")
            assert result == "source missing"

    def test_command_healthy(self, tmp_path):
        """Command exists — returns None."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "vault.yaml").write_text("name: test-vault\n")
        cmds = vault / "commands"
        cmds.mkdir()
        (cmds / "my-cmd.md").write_text("---\nname: my-cmd\n---\n")

        with mock.patch(
            "artifactr.cli.get_vault_by_name_or_path",
            return_value=str(vault),
        ):
            result = check_import_health("my-cmd", "command", "test-vault")
            assert result is None


# ---------------------------------------------------------------------------
# 6.4 KeyboardInterrupt handling test
# ---------------------------------------------------------------------------


class TestKeyboardInterrupt:
    """Tests for clean Ctrl-C exit."""

    def test_keyboard_interrupt_returns_130(self):
        """KeyboardInterrupt should result in exit code 130."""
        with mock.patch("artifactr.cli._main", side_effect=KeyboardInterrupt):
            result = main()
            assert result == 130
