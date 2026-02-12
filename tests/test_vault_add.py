"""Tests for vault add auto-naming and --set-default."""

from pathlib import Path
from unittest import mock

import pytest

from artifactr.catalog import add_vaults


class TestAutoNaming:
    """Tests for vault add auto-naming."""

    @mock.patch("artifactr.catalog.save_config")
    @mock.patch("artifactr.catalog.load_config")
    def test_first_vault_auto_named(self, mock_load, mock_save, tmp_path):
        """Verify first auto-named vault gets llm-vault-1."""
        vault_dir = tmp_path / "vault1"
        vault_dir.mkdir()

        mock_load.return_value = {
            "vaults": [],
            "vault_names": {},
            "default_vault": None,
            "default_tool": "claude-code",
        }

        result = add_vaults([str(vault_dir)])

        assert len(result["added"]) == 1
        assert result["names"][str(vault_dir.resolve())] == "llm-vault-1"

    @mock.patch("artifactr.catalog.save_config")
    @mock.patch("artifactr.catalog.load_config")
    def test_incrementing_counter(self, mock_load, mock_save, tmp_path):
        """Verify counter increments past existing llm-vault-N names."""
        vault_dir = tmp_path / "vault2"
        vault_dir.mkdir()

        mock_load.return_value = {
            "vaults": ["/existing"],
            "vault_names": {"/existing": "llm-vault-3"},
            "default_vault": "/existing",
            "default_tool": "claude-code",
        }

        result = add_vaults([str(vault_dir)])

        assert result["names"][str(vault_dir.resolve())] == "llm-vault-4"

    @mock.patch("artifactr.catalog.save_config")
    @mock.patch("artifactr.catalog.load_config")
    def test_multiple_vaults_auto_named(self, mock_load, mock_save, tmp_path):
        """Verify multiple vaults get unique auto-names."""
        vault1 = tmp_path / "vault_a"
        vault2 = tmp_path / "vault_b"
        vault1.mkdir()
        vault2.mkdir()

        mock_load.return_value = {
            "vaults": [],
            "vault_names": {},
            "default_vault": None,
            "default_tool": "claude-code",
        }

        result = add_vaults([str(vault1), str(vault2)])

        assert len(result["added"]) == 2
        names = list(result["names"].values())
        assert names[0] == "llm-vault-1"
        assert names[1] == "llm-vault-2"

    @mock.patch("artifactr.catalog.save_config")
    @mock.patch("artifactr.catalog.load_config")
    def test_explicit_name_still_works(self, mock_load, mock_save, tmp_path):
        """Verify explicit --name bypasses auto-naming."""
        vault_dir = tmp_path / "vault3"
        vault_dir.mkdir()

        mock_load.return_value = {
            "vaults": [],
            "vault_names": {},
            "default_vault": None,
            "default_tool": "claude-code",
        }

        result = add_vaults([str(vault_dir)], name="my-vault")

        assert result["names"][str(vault_dir.resolve())] == "my-vault"

    @mock.patch("artifactr.catalog.save_config")
    @mock.patch("artifactr.catalog.load_config")
    def test_duplicate_name_error_includes_path(self, mock_load, mock_save, tmp_path):
        """Verify duplicate name error mentions conflicting vault path."""
        vault_dir = tmp_path / "vault4"
        vault_dir.mkdir()

        mock_load.return_value = {
            "vaults": ["/existing/vault"],
            "vault_names": {"/existing/vault": "taken-name"},
            "default_vault": "/existing/vault",
            "default_tool": "claude-code",
        }

        result = add_vaults([str(vault_dir)], name="taken-name")

        assert len(result["errors"]) == 1
        assert "/existing/vault" in result["errors"][0]
        assert "art vault name" in result["errors"][0]


class TestSetDefaultFlag:
    """Tests for --set-default behavior (tested via CLI parsing)."""

    def test_set_default_flag_parsed(self):
        """Verify --set-default flag is accepted by argparse."""
        from artifactr.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["vault", "add", "/some/path", "--set-default"])
        assert args.set_default is True

    def test_set_default_flag_default_false(self):
        """Verify --set-default defaults to False."""
        from artifactr.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["vault", "add", "/some/path"])
        assert args.set_default is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
