"""Tests for art config backup command."""

import argparse
import zipfile
from pathlib import Path
from unittest import mock

import pytest
import yaml

from artifactr.catalog import backup_catalog
from artifactr.cli import create_parser, handle_config_backup


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_backup_args(**kwargs):
    defaults = {"output": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_config(tmp_path, vaults=None, vault_names=None, default_vault=None,
                 default_tool="opencode", nav_mode=None, tools=None):
    """Return a fake config dict."""
    if vaults is None:
        vaults = []
    if vault_names is None:
        vault_names = {}
    return {
        "vaults": vaults,
        "default_vault": default_vault,
        "default_tool": default_tool,
        "vault_names": vault_names,
        "tools": tools or {},
        "nav_mode": nav_mode,
    }


# ---------------------------------------------------------------------------
# backup_catalog business logic
# ---------------------------------------------------------------------------

def test_backup_errors_if_output_exists(tmp_path):
    """backup_catalog should error if the output file already exists."""
    existing = tmp_path / "backup.zip"
    existing.write_bytes(b"")
    config = _make_config(tmp_path)

    with mock.patch("artifactr.catalog.load_config", return_value=config):
        result = backup_catalog(str(existing))

    assert result["success"] is False
    assert "already exists" in result["error"]


def test_backup_no_vaults(tmp_path):
    """Backup with no registered vaults should produce archive with manifest and snapshot."""
    output = tmp_path / "backup.zip"
    config = _make_config(tmp_path)

    with mock.patch("artifactr.catalog.load_config", return_value=config):
        result = backup_catalog(str(output))

    assert result["success"] is True
    assert result["vault_count"] == 0
    assert output.exists()

    with zipfile.ZipFile(output) as zf:
        names = zf.namelist()
        assert "manifest.yaml" in names
        assert "config_snapshot.yaml" in names


def test_backup_all_vaults_included(tmp_path):
    """All registered vaults should appear in the archive."""
    vault1 = tmp_path / "vault1"
    vault2 = tmp_path / "vault2"
    for v in (vault1, vault2):
        (v / "skills" / "my-skill").mkdir(parents=True)
        (v / "skills" / "my-skill" / "artifact.md").write_text("# skill")
        (v / "commands").mkdir()

    output = tmp_path / "backup.zip"
    config = _make_config(
        tmp_path,
        vaults=[str(vault1), str(vault2)],
        vault_names={str(vault1): "personal", str(vault2): "work"},
    )

    with mock.patch("artifactr.catalog.load_config", return_value=config):
        result = backup_catalog(str(output))

    assert result["success"] is True
    assert result["vault_count"] == 2

    with zipfile.ZipFile(output) as zf:
        names = zf.namelist()
        # Both vaults named by their vault name
        assert any("personal/" in n for n in names)
        assert any("work/" in n for n in names)


def test_backup_config_snapshot_content(tmp_path):
    """config_snapshot.yaml should contain the right fields with vault name, not path."""
    vault1 = tmp_path / "myvault"
    vault1.mkdir()

    output = tmp_path / "backup.zip"
    config = _make_config(
        tmp_path,
        vaults=[str(vault1)],
        vault_names={str(vault1): "personal"},
        default_vault=str(vault1),
        default_tool="claude-code",
        nav_mode="flat",
        tools={"mytool": {"skills": ".mytool/skills"}},
    )

    with mock.patch("artifactr.catalog.load_config", return_value=config):
        result = backup_catalog(str(output))

    assert result["success"] is True

    with zipfile.ZipFile(output) as zf:
        snapshot = yaml.safe_load(zf.read("config_snapshot.yaml").decode())

    assert snapshot["default_vault_name"] == "personal"  # name, not path
    assert snapshot["default_tool"] == "claude-code"
    assert snapshot["nav_mode"] == "flat"
    assert "mytool" in snapshot["tools"]
    assert "format_version" in snapshot
    assert "created_at" in snapshot


def test_backup_snapshot_default_vault_name_null_when_no_default(tmp_path):
    """config_snapshot.yaml should have null default_vault_name when no default."""
    output = tmp_path / "backup.zip"
    config = _make_config(tmp_path, default_vault=None)

    with mock.patch("artifactr.catalog.load_config", return_value=config):
        result = backup_catalog(str(output))

    assert result["success"] is True
    with zipfile.ZipFile(output) as zf:
        snapshot = yaml.safe_load(zf.read("config_snapshot.yaml").decode())
    assert snapshot["default_vault_name"] is None


def test_backup_manifest_is_valid(tmp_path):
    """manifest.yaml should have format_version, created_at, and vaults list."""
    vault1 = tmp_path / "vault1"
    vault1.mkdir()
    output = tmp_path / "backup.zip"
    config = _make_config(
        tmp_path,
        vaults=[str(vault1)],
        vault_names={str(vault1): "personal"},
    )

    with mock.patch("artifactr.catalog.load_config", return_value=config):
        backup_catalog(str(output))

    with zipfile.ZipFile(output) as zf:
        manifest = yaml.safe_load(zf.read("manifest.yaml").decode())

    assert "format_version" in manifest
    assert "created_at" in manifest
    assert "vaults" in manifest
    assert manifest["vaults"][0]["name"] == "personal"
    assert manifest["vaults"][0]["dir"] == "personal"


def test_backup_vault_dirs_use_names_not_paths(tmp_path):
    """Vault directories in archive should be named by vault name, not absolute path."""
    vault1 = tmp_path / "very_long_absolute_path_vault"
    vault1.mkdir()
    (vault1 / "skills" / "s1").mkdir(parents=True)
    (vault1 / "skills" / "s1" / "artifact.md").write_text("hi")
    output = tmp_path / "backup.zip"
    config = _make_config(
        tmp_path,
        vaults=[str(vault1)],
        vault_names={str(vault1): "myvault"},
    )

    with mock.patch("artifactr.catalog.load_config", return_value=config):
        backup_catalog(str(output))

    with zipfile.ZipFile(output) as zf:
        names = zf.namelist()
    # Should have myvault/ prefix, NOT the absolute path
    assert any(n.startswith("myvault/") for n in names)
    assert not any(str(vault1) in n for n in names)


# ---------------------------------------------------------------------------
# handle_config_backup CLI handler
# ---------------------------------------------------------------------------

def test_handle_backup_default_filename(tmp_path, monkeypatch, capsys):
    """art config backup with no output arg should write to artifactr-backup-YYYYMMDD.zip."""
    monkeypatch.chdir(tmp_path)
    args = _make_backup_args()

    backup_result = {"success": True, "output": str(tmp_path / "artifactr-backup-20260226.zip"), "vault_count": 0, "error": None}

    with mock.patch("artifactr.catalog.backup_catalog", return_value=backup_result):
        rc = handle_config_backup(args)

    assert rc == 0
    out = capsys.readouterr().out
    assert "Backup written" in out


def test_handle_backup_custom_output(tmp_path, capsys):
    """art config backup my-backup.zip should use the given path."""
    custom = str(tmp_path / "my-backup.zip")
    args = _make_backup_args(output=custom)

    backup_result = {"success": True, "output": custom, "vault_count": 1, "error": None}

    with mock.patch("artifactr.catalog.backup_catalog", return_value=backup_result) as mock_bc:
        rc = handle_config_backup(args)

    assert rc == 0
    mock_bc.assert_called_once_with(custom)


def test_handle_backup_errors_on_existing_output(tmp_path, capsys):
    """handler should return 1 and print error when output already exists."""
    existing = str(tmp_path / "exists.zip")
    args = _make_backup_args(output=existing)

    backup_result = {"success": False, "output": None, "vault_count": 0, "error": f"Output file already exists: {existing}"}

    with mock.patch("artifactr.catalog.backup_catalog", return_value=backup_result):
        rc = handle_config_backup(args)

    assert rc == 1
    err = capsys.readouterr().err
    assert "already exists" in err
