"""Tests for vault init command."""

from pathlib import Path
from unittest import mock

import pytest

from artifactr.catalog import init_vault


class TestInitVault:
    """Tests for init_vault function."""

    @mock.patch("artifactr.catalog.save_config")
    @mock.patch("artifactr.catalog.load_config")
    def test_creates_new_directory_with_scaffolding(self, mock_load, mock_save, tmp_path):
        """Verify new directory is created with subdirs."""
        vault_dir = tmp_path / "new-vault"

        mock_load.return_value = {
            "vaults": [],
            "vault_names": {},
            "default_vault": None,
            "default_tool": "claude-code",
        }

        result = init_vault(str(vault_dir))

        assert result["created"] is True
        assert len(result["added"]) == 1
        assert (vault_dir / "skills").is_dir()
        assert (vault_dir / "agents").is_dir()
        assert (vault_dir / "commands").is_dir()

    @mock.patch("artifactr.catalog.save_config")
    @mock.patch("artifactr.catalog.load_config")
    def test_existing_directory_idempotent(self, mock_load, mock_save, tmp_path):
        """Verify existing directory is registered without modifying contents."""
        vault_dir = tmp_path / "existing-vault"
        vault_dir.mkdir()
        # Create a file that shouldn't be touched
        (vault_dir / "README.md").write_text("existing content")

        mock_load.return_value = {
            "vaults": [],
            "vault_names": {},
            "default_vault": None,
            "default_tool": "claude-code",
        }

        result = init_vault(str(vault_dir))

        assert result["created"] is False
        assert len(result["added"]) == 1
        assert (vault_dir / "README.md").read_text() == "existing content"

    @mock.patch("artifactr.catalog.save_config")
    @mock.patch("artifactr.catalog.load_config")
    def test_init_with_name(self, mock_load, mock_save, tmp_path):
        """Verify vault is registered with explicit name."""
        vault_dir = tmp_path / "named-vault"

        mock_load.return_value = {
            "vaults": [],
            "vault_names": {},
            "default_vault": None,
            "default_tool": "claude-code",
        }

        result = init_vault(str(vault_dir), name="my-vault")

        assert result["names"][str(vault_dir.resolve())] == "my-vault"

    @mock.patch("artifactr.catalog.save_config")
    @mock.patch("artifactr.catalog.load_config")
    def test_init_auto_names(self, mock_load, mock_save, tmp_path):
        """Verify vault is auto-named when no name provided."""
        vault_dir = tmp_path / "auto-vault"

        mock_load.return_value = {
            "vaults": [],
            "vault_names": {},
            "default_vault": None,
            "default_tool": "claude-code",
        }

        result = init_vault(str(vault_dir))

        assert result["names"][str(vault_dir.resolve())] == "llm-vault-1"

    @mock.patch("artifactr.catalog.save_config")
    @mock.patch("artifactr.catalog.load_config")
    def test_already_registered(self, mock_load, mock_save, tmp_path):
        """Verify already registered vault is reported as skipped."""
        vault_dir = tmp_path / "reg-vault"
        vault_dir.mkdir()

        mock_load.return_value = {
            "vaults": [str(vault_dir.resolve())],
            "vault_names": {str(vault_dir.resolve()): "llm-vault-1"},
            "default_vault": str(vault_dir.resolve()),
            "default_tool": "claude-code",
        }

        result = init_vault(str(vault_dir))

        assert result["created"] is False
        assert len(result["added"]) == 0
        assert len(result["skipped"]) == 1


class TestVaultInitCLIParsing:
    """Tests for vault init CLI argument parsing."""

    def test_vault_init_arguments(self):
        """Verify vault init accepts required arguments."""
        from artifactr.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["vault", "init", "/path/to/vault"])
        assert args.vault_command == "init"
        assert args.target_dir == "/path/to/vault"

    def test_vault_init_with_name(self):
        """Verify --name flag is parsed."""
        from artifactr.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["vault", "init", "/path", "--name", "my-vault"])
        assert args.name == "my-vault"

    def test_vault_init_with_set_default(self):
        """Verify --set-default flag is parsed."""
        from artifactr.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["vault", "init", "/path", "--set-default"])
        assert args.set_default is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
