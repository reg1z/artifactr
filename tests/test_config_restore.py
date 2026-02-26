"""Tests for art config restore command."""

import argparse
import zipfile
from pathlib import Path
from unittest import mock

import pytest
import yaml

from artifactr.catalog import restore_catalog
from artifactr.cli import create_parser, handle_config_restore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_restore_args(archive):
    return argparse.Namespace(archive=archive)


def _make_backup_zip(tmp_path, vaults, snapshot=None, include_manifest=True, include_snapshot=True):
    """Build a backup archive for testing.

    vaults: list of dicts with keys 'name' (and optionally 'skills', 'commands')
    snapshot: optional dict; defaults to reasonable values
    """
    zip_path = tmp_path / "backup.zip"
    if snapshot is None:
        snapshot = {
            "format_version": 1,
            "created_at": "2026-02-26T00:00:00+00:00",
            "default_vault_name": vaults[0]["name"] if vaults else None,
            "default_tool": "opencode",
            "nav_mode": None,
            "tools": {},
        }

    manifest_entries = [{"name": v["name"], "dir": v["name"]} for v in vaults]

    with zipfile.ZipFile(zip_path, "w") as zf:
        for v in vaults:
            name = v["name"]
            # Add a skill file
            skill_content = v.get("skill_content", "# test skill")
            zf.writestr(f"{name}/skills/test-skill/artifact.md", skill_content)

        if include_manifest:
            manifest_data = {
                "format_version": 1,
                "created_at": "2026-02-26T00:00:00+00:00",
                "vaults": manifest_entries,
            }
            zf.writestr("manifest.yaml", yaml.dump(manifest_data))

        if include_snapshot:
            zf.writestr("config_snapshot.yaml", yaml.dump(snapshot))

    return zip_path


# ---------------------------------------------------------------------------
# restore_catalog business logic
# ---------------------------------------------------------------------------

def test_restore_valid_archive(tmp_path):
    """restore_catalog should extract vaults and register them."""
    zip_path = _make_backup_zip(tmp_path, [{"name": "personal"}])

    config = {"vaults": [], "default_vault": None, "default_tool": "opencode",
              "vault_names": {}, "tools": {}, "nav_mode": None}

    with mock.patch("artifactr.catalog.load_config", return_value=config), \
         mock.patch("artifactr.catalog.save_config") as mock_save, \
         mock.patch("artifactr.catalog.add_vaults") as mock_add, \
         mock.patch("artifactr.config.get_config_dir", return_value=tmp_path / "config"):
        mock_add.return_value = {"added": [str(tmp_path / "config" / "vaults" / "personal")], "skipped": [], "errors": [], "names": {"x": "personal"}}
        result = restore_catalog(str(zip_path))

    assert result["success"] is True
    assert len(result["extracted"]) == 1
    assert result["extracted"][0]["name"] == "personal"


def test_restore_extraction_location(tmp_path):
    """Vaults should be extracted to config_dir/vaults/<vault-name>/."""
    zip_path = _make_backup_zip(tmp_path, [{"name": "myvault"}])
    config_dir = tmp_path / "config"

    config = {"vaults": [], "default_vault": None, "default_tool": "opencode",
              "vault_names": {}, "tools": {}, "nav_mode": None}

    with mock.patch("artifactr.catalog.load_config", return_value=config), \
         mock.patch("artifactr.catalog.save_config"), \
         mock.patch("artifactr.catalog.add_vaults") as mock_add, \
         mock.patch("artifactr.config.get_config_dir", return_value=config_dir):
        extracted_path = config_dir / "vaults" / "myvault"
        mock_add.return_value = {"added": [str(extracted_path)], "skipped": [], "errors": [], "names": {str(extracted_path): "myvault"}}
        restore_catalog(str(zip_path))
        call_args = mock_add.call_args_list[0]

    assert "myvault" in call_args[0][0][0]
    assert "vaults" in call_args[0][0][0]


def test_restore_name_conflict_rename(tmp_path):
    """When vault name conflicts, it should be renamed with -1 suffix."""
    zip_path = _make_backup_zip(tmp_path, [{"name": "personal"}])

    # Existing vault with same name
    existing_vault = tmp_path / "existing"
    config = {
        "vaults": [str(existing_vault)],
        "default_vault": None,
        "default_tool": "opencode",
        "vault_names": {str(existing_vault): "personal"},
        "tools": {}, "nav_mode": None,
    }

    with mock.patch("artifactr.catalog.load_config", return_value=config), \
         mock.patch("artifactr.catalog.save_config"), \
         mock.patch("artifactr.catalog.add_vaults") as mock_add, \
         mock.patch("artifactr.config.get_config_dir", return_value=tmp_path / "config"):
        renamed_path = tmp_path / "config" / "vaults" / "personal-1"
        mock_add.return_value = {"added": [str(renamed_path)], "skipped": [], "errors": [], "names": {str(renamed_path): "personal-1"}}
        result = restore_catalog(str(zip_path))

    assert result["success"] is True
    assert result["renames"].get("personal") == "personal-1"


def test_restore_no_conflict_original_name_used(tmp_path):
    """When no name conflict, original vault name should be used."""
    zip_path = _make_backup_zip(tmp_path, [{"name": "work"}])

    config = {"vaults": [], "default_vault": None, "default_tool": "opencode",
              "vault_names": {}, "tools": {}, "nav_mode": None}

    with mock.patch("artifactr.catalog.load_config", return_value=config), \
         mock.patch("artifactr.catalog.save_config"), \
         mock.patch("artifactr.catalog.add_vaults") as mock_add, \
         mock.patch("artifactr.config.get_config_dir", return_value=tmp_path / "config"):
        extracted_path = tmp_path / "config" / "vaults" / "work"
        mock_add.return_value = {"added": [str(extracted_path)], "skipped": [], "errors": [], "names": {str(extracted_path): "work"}}
        result = restore_catalog(str(zip_path))

    assert "work" not in result["renames"]
    assert result["extracted"][0]["name"] == "work"


def test_restore_config_settings_applied(tmp_path):
    """restore_catalog should apply default_tool, nav_mode, and tools from snapshot."""
    snapshot = {
        "format_version": 1,
        "created_at": "2026-02-26T00:00:00+00:00",
        "default_vault_name": "personal",
        "default_tool": "claude-code",
        "nav_mode": "flat",
        "tools": {"mytool": {"skills": ".mytool/skills"}},
    }
    zip_path = _make_backup_zip(tmp_path, [{"name": "personal"}], snapshot=snapshot)

    config = {"vaults": [], "default_vault": None, "default_tool": "opencode",
              "vault_names": {}, "tools": {}, "nav_mode": None}
    saved_config = {}

    def fake_load():
        return dict(config)

    def fake_save(c):
        saved_config.update(c)

    with mock.patch("artifactr.catalog.load_config", side_effect=fake_load), \
         mock.patch("artifactr.catalog.save_config", side_effect=fake_save), \
         mock.patch("artifactr.catalog.add_vaults") as mock_add, \
         mock.patch("artifactr.config.get_config_dir", return_value=tmp_path / "config"):
        extracted_path = tmp_path / "config" / "vaults" / "personal"
        mock_add.return_value = {"added": [str(extracted_path)], "skipped": [], "errors": [], "names": {str(extracted_path): "personal"}}
        restore_catalog(str(zip_path))

    assert saved_config.get("default_tool") == "claude-code"
    assert saved_config.get("nav_mode") == "flat"
    assert "mytool" in saved_config.get("tools", {})


def test_restore_default_vault_set(tmp_path):
    """restore_catalog should set default_vault to the extracted vault's path."""
    snapshot = {
        "format_version": 1,
        "created_at": "2026-02-26T00:00:00+00:00",
        "default_vault_name": "personal",
        "default_tool": "opencode",
        "nav_mode": None,
        "tools": {},
    }
    zip_path = _make_backup_zip(tmp_path, [{"name": "personal"}], snapshot=snapshot)

    config = {"vaults": [], "default_vault": None, "default_tool": "opencode",
              "vault_names": {}, "tools": {}, "nav_mode": None}
    saved_config = {}

    def fake_load():
        return dict(config)

    def fake_save(c):
        saved_config.update(c)

    extracted_path = tmp_path / "config" / "vaults" / "personal"

    with mock.patch("artifactr.catalog.load_config", side_effect=fake_load), \
         mock.patch("artifactr.catalog.save_config", side_effect=fake_save), \
         mock.patch("artifactr.catalog.add_vaults") as mock_add, \
         mock.patch("artifactr.config.get_config_dir", return_value=tmp_path / "config"):
        mock_add.return_value = {"added": [str(extracted_path)], "skipped": [], "errors": [], "names": {str(extracted_path): "personal"}}
        result = restore_catalog(str(zip_path))

    assert saved_config.get("default_vault") == str(extracted_path)


def test_restore_default_vault_set_after_rename(tmp_path):
    """default_vault should point to renamed vault path when a name conflict occurred."""
    snapshot = {
        "format_version": 1,
        "created_at": "2026-02-26T00:00:00+00:00",
        "default_vault_name": "personal",
        "default_tool": "opencode",
        "nav_mode": None,
        "tools": {},
    }
    zip_path = _make_backup_zip(tmp_path, [{"name": "personal"}], snapshot=snapshot)

    existing_vault = tmp_path / "existing"
    config = {
        "vaults": [str(existing_vault)],
        "default_vault": None,
        "default_tool": "opencode",
        "vault_names": {str(existing_vault): "personal"},
        "tools": {}, "nav_mode": None,
    }
    saved_config = {}

    def fake_load():
        return dict(config)

    def fake_save(c):
        saved_config.update(c)

    renamed_path = tmp_path / "config" / "vaults" / "personal-1"

    with mock.patch("artifactr.catalog.load_config", side_effect=fake_load), \
         mock.patch("artifactr.catalog.save_config", side_effect=fake_save), \
         mock.patch("artifactr.catalog.add_vaults") as mock_add, \
         mock.patch("artifactr.config.get_config_dir", return_value=tmp_path / "config"):
        mock_add.return_value = {"added": [str(renamed_path)], "skipped": [], "errors": [], "names": {str(renamed_path): "personal-1"}}
        result = restore_catalog(str(zip_path))

    assert saved_config.get("default_vault") == str(renamed_path)


def test_restore_missing_default_vault_name_warns(tmp_path):
    """If default_vault_name not in archive vaults, emit a warning."""
    snapshot = {
        "format_version": 1,
        "created_at": "2026-02-26T00:00:00+00:00",
        "default_vault_name": "nonexistent-vault",
        "default_tool": "opencode",
        "nav_mode": None,
        "tools": {},
    }
    zip_path = _make_backup_zip(tmp_path, [{"name": "personal"}], snapshot=snapshot)

    config = {"vaults": [], "default_vault": None, "default_tool": "opencode",
              "vault_names": {}, "tools": {}, "nav_mode": None}

    with mock.patch("artifactr.catalog.load_config", return_value=config), \
         mock.patch("artifactr.catalog.save_config"), \
         mock.patch("artifactr.catalog.add_vaults") as mock_add, \
         mock.patch("artifactr.config.get_config_dir", return_value=tmp_path / "config"):
        extracted_path = tmp_path / "config" / "vaults" / "personal"
        mock_add.return_value = {"added": [str(extracted_path)], "skipped": [], "errors": [], "names": {str(extracted_path): "personal"}}
        result = restore_catalog(str(zip_path))

    assert result["success"] is True
    assert any("nonexistent-vault" in w for w in result["warnings"])


def test_restore_missing_archive_error(tmp_path):
    """restore_catalog should return error if archive doesn't exist."""
    result = restore_catalog(str(tmp_path / "nonexistent.zip"))
    assert result["success"] is False
    assert "not found" in result["error"].lower() or "Archive" in result["error"]


def test_restore_invalid_zip_error(tmp_path):
    """restore_catalog should error on non-zip files."""
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"not a zip file")
    result = restore_catalog(str(bad))
    assert result["success"] is False
    assert "not a valid zip" in result["error"].lower()


def test_restore_missing_manifest_error(tmp_path):
    """restore_catalog should error if archive has no manifest.yaml."""
    zip_path = _make_backup_zip(tmp_path, [{"name": "personal"}], include_manifest=False)
    result = restore_catalog(str(zip_path))
    assert result["success"] is False
    assert "manifest.yaml" in result["error"]


def test_restore_missing_snapshot_error(tmp_path):
    """restore_catalog should error if archive has no config_snapshot.yaml."""
    zip_path = _make_backup_zip(tmp_path, [{"name": "personal"}], include_snapshot=False)
    result = restore_catalog(str(zip_path))
    assert result["success"] is False
    assert "config_snapshot.yaml" in result["error"]


# ---------------------------------------------------------------------------
# handle_config_restore CLI handler
# ---------------------------------------------------------------------------

def test_handle_restore_success(tmp_path, capsys):
    """Successful restore should print extracted vaults and return 0."""
    args = _make_restore_args(archive=str(tmp_path / "backup.zip"))

    restore_result = {
        "success": True,
        "extracted": [{"name": "personal", "path": "/home/user/.config/artifactr/vaults/personal"}],
        "renames": {},
        "warnings": [],
        "errors": [],
        "error": None,
    }

    with mock.patch("artifactr.catalog.restore_catalog", return_value=restore_result):
        rc = handle_config_restore(args)

    assert rc == 0
    out = capsys.readouterr().out
    assert "personal" in out
    assert "Restore complete" in out


def test_handle_restore_reports_renames(tmp_path, capsys):
    """Renames should be reported in the output."""
    args = _make_restore_args(archive=str(tmp_path / "backup.zip"))

    restore_result = {
        "success": True,
        "extracted": [{"name": "personal-1", "path": "/home/.config/artifactr/vaults/personal-1"}],
        "renames": {"personal": "personal-1"},
        "warnings": [],
        "errors": [],
        "error": None,
    }

    with mock.patch("artifactr.catalog.restore_catalog", return_value=restore_result):
        rc = handle_config_restore(args)

    assert rc == 0
    out = capsys.readouterr().out
    assert "personal" in out
    assert "personal-1" in out


def test_handle_restore_reports_warnings(tmp_path, capsys):
    """Warnings should appear in output."""
    args = _make_restore_args(archive=str(tmp_path / "backup.zip"))

    restore_result = {
        "success": True,
        "extracted": [],
        "renames": {},
        "warnings": ["default_vault_name 'nonexistent' not found in archive"],
        "errors": [],
        "error": None,
    }

    with mock.patch("artifactr.catalog.restore_catalog", return_value=restore_result):
        rc = handle_config_restore(args)

    assert rc == 0
    out = capsys.readouterr().out
    assert "nonexistent" in out


def test_handle_restore_missing_archive(tmp_path, capsys):
    """Missing archive should return 1 with error message."""
    args = _make_restore_args(archive=str(tmp_path / "nonexistent.zip"))

    restore_result = {
        "success": False,
        "extracted": [],
        "renames": {},
        "warnings": [],
        "errors": [],
        "error": "Archive not found: /tmp/nonexistent.zip",
    }

    with mock.patch("artifactr.catalog.restore_catalog", return_value=restore_result):
        rc = handle_config_restore(args)

    assert rc == 1
    err = capsys.readouterr().err
    assert "Archive not found" in err


def test_handle_restore_missing_manifest(tmp_path, capsys):
    """Missing manifest should return 1 with error message."""
    args = _make_restore_args(archive=str(tmp_path / "backup.zip"))

    restore_result = {
        "success": False,
        "extracted": [],
        "renames": {},
        "warnings": [],
        "errors": [],
        "error": "Archive does not contain manifest.yaml",
    }

    with mock.patch("artifactr.catalog.restore_catalog", return_value=restore_result):
        rc = handle_config_restore(args)

    assert rc == 1
    err = capsys.readouterr().err
    assert "manifest.yaml" in err


def test_handle_restore_requires_archive_arg():
    """art config restore without argument should fail at parse time."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["config", "restore"])
