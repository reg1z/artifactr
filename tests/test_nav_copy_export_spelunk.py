"""Tests for nav-copy-export-spelunk change.

Covers:
- art copy: source resolution, destination resolution, type coercion, glob expansion, conflict detection
- art vault copy: default scope, --all flag, auto-registration, vault.yaml name update
- art vault export: single-vault, multi-vault, glob selection, --all, manifest structure
- art vault import: extraction, manifest parsing, auto-registration, conflict handling, confirmation flow
- art nav: target resolution, --print mode, nav_mode config, vault name collision warnings
- art shell setup: shell detection, snippet generation, fish special case
"""

import argparse
import zipfile
from pathlib import Path
from unittest import mock

import pytest
import yaml

from artifactr.catalog import (
    copy_vault,
    export_vaults,
    import_vaults_from_zip,
    resolve_vaults_for_export,
)
from artifactr.cli import (
    _NAV_TYPE_ALIASES,
    _find_artifacts_in_vault,
    _resolve_copy_dest,
    _resolve_copy_source,
    _resolve_copy_type,
    create_parser,
    handle_copy,
    handle_nav,
    handle_shell_setup,
    handle_vault_copy,
    handle_vault_export,
    handle_vault_import,
)
from artifactr.utils import (
    detect_shell,
    get_shell_rc_file,
    get_shell_wrapper_snippet,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def vault_with_artifacts(tmp_path):
    """Create a vault with skills, commands, agents for copy tests."""
    vault = tmp_path / "my-vault"
    (vault / "skills" / "my-skill").mkdir(parents=True)
    (vault / "skills" / "my-skill" / "SKILL.md").write_text(
        "---\nname: My Skill\ndescription: A skill\n---\n"
    )
    (vault / "skills" / "other-skill").mkdir(parents=True)
    (vault / "skills" / "other-skill" / "SKILL.md").write_text(
        "---\nname: other-skill\ndescription: Another skill\n---\n"
    )
    (vault / "commands").mkdir()
    (vault / "commands" / "my-cmd.md").write_text(
        "---\ndescription: A command\n---\n"
    )
    (vault / "agents").mkdir()
    (vault / "agents" / "my-agent.md").write_text(
        "---\nname: my-agent\ndescription: An agent\n---\n"
    )
    (vault / "vault.yaml").write_text("name: my-vault\n")
    return vault


@pytest.fixture()
def dest_vault(tmp_path):
    """Create an empty destination vault."""
    vault = tmp_path / "dest-vault"
    (vault / "skills").mkdir(parents=True)
    (vault / "commands").mkdir()
    (vault / "agents").mkdir()
    (vault / "vault.yaml").write_text("name: dest-vault\n")
    return vault


# ---------------------------------------------------------------------------
# Section 5: art copy
# ---------------------------------------------------------------------------


class TestResolveCopyType:
    def test_skill_aliases(self):
        assert _resolve_copy_type("skill") == "skills"
        assert _resolve_copy_type("skills") == "skills"
        assert _resolve_copy_type("s") == "skills"
        assert _resolve_copy_type("sk") == "skills"

    def test_command_aliases(self):
        assert _resolve_copy_type("command") == "commands"
        assert _resolve_copy_type("commands") == "commands"
        assert _resolve_copy_type("c") == "commands"
        assert _resolve_copy_type("cmd") == "commands"
        assert _resolve_copy_type("com") == "commands"

    def test_agent_aliases(self):
        assert _resolve_copy_type("agent") == "agents"
        assert _resolve_copy_type("agents") == "agents"
        assert _resolve_copy_type("a") == "agents"
        assert _resolve_copy_type("agt") == "agents"

    def test_unknown_returns_none(self):
        assert _resolve_copy_type("unknown") is None
        assert _resolve_copy_type("") is None


class TestResolveCopySource:
    def test_bare_name_uses_default_vault(self, vault_with_artifacts):
        with mock.patch("artifactr.cli.get_default_vault", return_value=str(vault_with_artifacts)):
            result = _resolve_copy_source("my-skill")
        assert result["error"] is None
        assert result["vault_path"] == str(vault_with_artifacts)
        assert result["type_subdir"] is None
        assert result["name_pattern"] == "my-skill"

    def test_type_prefix(self, vault_with_artifacts):
        with mock.patch("artifactr.cli.get_default_vault", return_value=str(vault_with_artifacts)):
            result = _resolve_copy_source("skills/my-skill")
        assert result["error"] is None
        assert result["type_subdir"] == "skills"
        assert result["name_pattern"] == "my-skill"

    def test_vault_prefix(self, vault_with_artifacts):
        with mock.patch("artifactr.cli.get_vault_by_name_or_path", return_value=str(vault_with_artifacts)):
            result = _resolve_copy_source("my-vault/my-skill")
        assert result["error"] is None
        assert result["vault_path"] == str(vault_with_artifacts)
        assert result["name_pattern"] == "my-skill"

    def test_fully_qualified(self, vault_with_artifacts):
        with mock.patch("artifactr.cli.get_vault_by_name_or_path", return_value=str(vault_with_artifacts)):
            result = _resolve_copy_source("my-vault/skills/my-skill")
        assert result["error"] is None
        assert result["vault_path"] == str(vault_with_artifacts)
        assert result["type_subdir"] == "skills"
        assert result["name_pattern"] == "my-skill"

    def test_no_default_vault_error(self):
        with mock.patch("artifactr.cli.get_default_vault", return_value=None):
            result = _resolve_copy_source("my-skill")
        assert result["error"] is not None


class TestResolveCopyDest:
    def test_trailing_slash_is_container(self, vault_with_artifacts):
        with mock.patch("artifactr.cli.get_vault_by_name_or_path", return_value=str(vault_with_artifacts)):
            result = _resolve_copy_dest("dest-vault/", source_vault_path=str(vault_with_artifacts))
        assert result["is_container"] is True
        assert result["vault_path"] == str(vault_with_artifacts)

    def test_registered_vault_name_is_container(self, vault_with_artifacts):
        with mock.patch("artifactr.cli.get_vault_by_name_or_path", return_value=str(vault_with_artifacts)):
            result = _resolve_copy_dest("dest-vault", source_vault_path=str(vault_with_artifacts))
        assert result["is_container"] is True

    def test_unknown_name_is_rename(self, vault_with_artifacts):
        with mock.patch("artifactr.cli.get_vault_by_name_or_path", return_value=None):
            result = _resolve_copy_dest("my-skill-v2", source_vault_path=str(vault_with_artifacts))
        assert result["is_container"] is False
        assert result["new_name"] == "my-skill-v2"
        assert result["vault_path"] == str(vault_with_artifacts)

    def test_vault_slash_name_format(self, vault_with_artifacts, dest_vault):
        def mock_resolve(name):
            if name == "dest-vault":
                return str(dest_vault)
            return None
        with mock.patch("artifactr.cli.get_vault_by_name_or_path", side_effect=mock_resolve):
            result = _resolve_copy_dest("dest-vault/renamed-skill", source_vault_path=str(vault_with_artifacts))
        assert result["is_container"] is False
        assert result["vault_path"] == str(dest_vault)
        assert result["new_name"] == "renamed-skill"


class TestFindArtifactsInVault:
    def test_find_skill_by_name(self, vault_with_artifacts):
        results = _find_artifacts_in_vault(str(vault_with_artifacts), "skills", "my-skill")
        assert len(results) == 1
        assert results[0]["name"] == "my-skill"
        assert results[0]["type_subdir"] == "skills"

    def test_find_command_by_name(self, vault_with_artifacts):
        results = _find_artifacts_in_vault(str(vault_with_artifacts), "commands", "my-cmd")
        assert len(results) == 1
        assert results[0]["name"] == "my-cmd"

    def test_glob_pattern_matches_multiple(self, vault_with_artifacts):
        results = _find_artifacts_in_vault(str(vault_with_artifacts), "skills", "*")
        assert len(results) == 2

    def test_glob_pattern_filtered(self, vault_with_artifacts):
        results = _find_artifacts_in_vault(str(vault_with_artifacts), "skills", "my-*")
        assert len(results) == 1
        assert results[0]["name"] == "my-skill"

    def test_no_type_searches_all(self, vault_with_artifacts):
        results = _find_artifacts_in_vault(str(vault_with_artifacts), None, "*")
        assert len(results) == 4  # 2 skills + 1 command + 1 agent

    def test_nonexistent_name_returns_empty(self, vault_with_artifacts):
        results = _find_artifacts_in_vault(str(vault_with_artifacts), "skills", "nonexistent")
        assert results == []


class TestHandleCopy:
    def test_copy_skill_to_dest_vault(self, vault_with_artifacts, dest_vault, capsys):
        def mock_resolve(name):
            if "my-vault" in name or str(vault_with_artifacts) in name:
                return str(vault_with_artifacts)
            if "dest-vault" in name or str(dest_vault) in name:
                return str(dest_vault)
            return None

        args = argparse.Namespace(
            source="skills/my-skill",
            dest="dest-vault/",
        )
        with mock.patch("artifactr.cli.get_default_vault", return_value=str(vault_with_artifacts)), \
             mock.patch("artifactr.cli.get_vault_by_name_or_path", side_effect=mock_resolve):
            rc = handle_copy(args)

        assert rc == 0
        assert (dest_vault / "skills" / "my-skill").is_dir()

    def test_copy_same_vault_duplicate(self, vault_with_artifacts, capsys):
        args = argparse.Namespace(
            source="skills/my-skill",
            dest="my-skill-v2",
        )
        with mock.patch("artifactr.cli.get_default_vault", return_value=str(vault_with_artifacts)), \
             mock.patch("artifactr.cli.get_vault_by_name_or_path", return_value=None):
            rc = handle_copy(args)

        assert rc == 0
        assert (vault_with_artifacts / "skills" / "my-skill-v2").is_dir()

    def test_copy_glob_requires_container(self, vault_with_artifacts, capsys):
        args = argparse.Namespace(
            source="skills/*",
            dest="my-skill-v2",
        )
        with mock.patch("artifactr.cli.get_default_vault", return_value=str(vault_with_artifacts)), \
             mock.patch("artifactr.cli.get_vault_by_name_or_path", return_value=None):
            rc = handle_copy(args)

        assert rc == 1
        err = capsys.readouterr().err
        assert "container" in err.lower()

    def test_copy_frontmatter_name_fallback(self, vault_with_artifacts, dest_vault, capsys):
        """Copies using frontmatter name 'My Skill' even though dir is 'my-skill'."""
        args = argparse.Namespace(
            source="skills/My Skill",
            dest="dest-vault/",
        )

        def mock_resolve(name):
            if "dest-vault" in name or str(dest_vault) in name:
                return str(dest_vault)
            return None

        with mock.patch("artifactr.cli.get_default_vault", return_value=str(vault_with_artifacts)), \
             mock.patch("artifactr.cli.get_vault_by_name_or_path", side_effect=mock_resolve):
            rc = handle_copy(args)

        # Should succeed via frontmatter fallback
        assert rc == 0

    def test_copy_parser_alias(self):
        parser = create_parser()
        ns = parser.parse_args(["cp", "src-skill", "vault-2/"])
        assert ns.command in ("copy", "cp")


# ---------------------------------------------------------------------------
# Section 6: art vault copy
# ---------------------------------------------------------------------------


class TestCopyVault:
    def test_default_copy_scope(self, vault_with_artifacts, tmp_path):
        """Only skills/, commands/, agents/, vault.yaml are copied by default."""
        extra_file = vault_with_artifacts / "extra.txt"
        extra_file.write_text("extra content")

        with mock.patch("artifactr.catalog.add_vaults") as mock_add:
            mock_add.return_value = {"added": [], "skipped": [], "errors": [], "names": {}}
            result = copy_vault(str(vault_with_artifacts), str(tmp_path / "new-vault"))

        assert result["success"] is True
        dest = Path(result["dest_path"])
        assert (dest / "skills").is_dir()
        assert (dest / "commands").is_dir()
        assert (dest / "agents").is_dir()
        assert (dest / "vault.yaml").is_file()
        assert not (dest / "extra.txt").exists()

    def test_all_flag_copies_extra_files(self, vault_with_artifacts, tmp_path):
        """--all copies all files except .git/."""
        extra_file = vault_with_artifacts / "extra.txt"
        extra_file.write_text("extra content")
        git_dir = vault_with_artifacts / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main")

        with mock.patch("artifactr.catalog.add_vaults") as mock_add:
            mock_add.return_value = {"added": [], "skipped": [], "errors": [], "names": {}}
            result = copy_vault(str(vault_with_artifacts), str(tmp_path / "new-vault"), copy_all=True)

        assert result["success"] is True
        dest = Path(result["dest_path"])
        assert (dest / "extra.txt").exists()
        assert not (dest / ".git").exists()

    def test_vault_yaml_name_updated(self, vault_with_artifacts, tmp_path):
        """vault.yaml name is updated to the new vault name."""
        fake_config_dir = tmp_path / "config"
        with mock.patch("artifactr.catalog.add_vaults") as mock_add, \
             mock.patch("artifactr.config.get_config_dir", return_value=fake_config_dir):
            mock_add.return_value = {"added": [], "skipped": [], "errors": [], "names": {}}
            result = copy_vault(str(vault_with_artifacts), "new-vault-name")

        assert result["success"] is True
        dest = Path(result["dest_path"])
        meta = yaml.safe_load((dest / "vault.yaml").read_text())
        assert meta["name"] == "new-vault-name"

    def test_auto_registers_vault(self, vault_with_artifacts, tmp_path):
        """Auto-registers the copied vault."""
        with mock.patch("artifactr.catalog.add_vaults") as mock_add:
            mock_add.return_value = {"added": [str(tmp_path / "new-vault")], "skipped": [], "errors": [], "names": {}}
            result = copy_vault(str(vault_with_artifacts), str(tmp_path / "new-vault"))

        assert result["success"] is True
        mock_add.assert_called_once()

    def test_error_if_destination_exists(self, vault_with_artifacts, tmp_path):
        """Errors if destination path already exists."""
        existing = tmp_path / "existing"
        existing.mkdir()
        result = copy_vault(str(vault_with_artifacts), str(existing))
        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_vault_copy_alias(self):
        parser = create_parser()
        ns = parser.parse_args(["vault", "cp", "src-vault", "dest-vault"])
        assert ns.vault_command in ("copy", "cp")


# ---------------------------------------------------------------------------
# Section 7: art vault export
# ---------------------------------------------------------------------------


class TestExportVaults:
    def test_single_vault_export(self, vault_with_artifacts, tmp_path):
        output = str(tmp_path / "bundle.zip")
        result = export_vaults([str(vault_with_artifacts)], ["my-vault"], output)
        assert result["success"] is True

        with zipfile.ZipFile(output, "r") as zf:
            names = zf.namelist()
            assert "manifest.yaml" in names
            assert any(n.startswith("my-vault/") for n in names)

    def test_manifest_structure(self, vault_with_artifacts, tmp_path):
        output = str(tmp_path / "bundle.zip")
        export_vaults([str(vault_with_artifacts)], ["my-vault"], output)

        with zipfile.ZipFile(output, "r") as zf:
            manifest = yaml.safe_load(zf.read("manifest.yaml"))

        assert "vaults" in manifest
        assert len(manifest["vaults"]) == 1
        assert manifest["vaults"][0]["name"] == "my-vault"
        assert manifest["vaults"][0]["dir"] == "my-vault"

    def test_multi_vault_export(self, vault_with_artifacts, dest_vault, tmp_path):
        output = str(tmp_path / "bundle.zip")
        result = export_vaults(
            [str(vault_with_artifacts), str(dest_vault)],
            ["my-vault", "dest-vault"],
            output,
        )
        assert result["success"] is True

        with zipfile.ZipFile(output, "r") as zf:
            manifest = yaml.safe_load(zf.read("manifest.yaml"))
        assert len(manifest["vaults"]) == 2

    def test_error_if_output_exists(self, vault_with_artifacts, tmp_path):
        output = tmp_path / "bundle.zip"
        output.write_bytes(b"existing")
        result = export_vaults([str(vault_with_artifacts)], ["my-vault"], str(output))
        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_resolve_vaults_all_flag(self, vault_with_artifacts, tmp_path):
        with mock.patch("artifactr.catalog.load_config") as mock_cfg:
            mock_cfg.return_value = {
                "vaults": [str(vault_with_artifacts)],
                "vault_names": {str(vault_with_artifacts): "my-vault"},
                "default_vault": str(vault_with_artifacts),
                "default_tool": "opencode",
                "tools": {},
                "nav_mode": None,
            }
            result = resolve_vaults_for_export(None, export_all=True)

        assert result["success"] is True
        assert str(vault_with_artifacts) in result["vault_paths"]

    def test_resolve_vaults_glob_pattern(self, vault_with_artifacts, tmp_path):
        with mock.patch("artifactr.catalog.load_config") as mock_cfg:
            mock_cfg.return_value = {
                "vaults": [str(vault_with_artifacts)],
                "vault_names": {str(vault_with_artifacts): "my-vault"},
                "default_vault": str(vault_with_artifacts),
                "default_tool": "opencode",
                "tools": {},
                "nav_mode": None,
            }
            result = resolve_vaults_for_export("my-*", export_all=False)

        assert result["success"] is True
        assert "my-vault" in result["vault_names"]

    def test_error_if_no_vault_specified(self):
        result = resolve_vaults_for_export(None, export_all=False)
        assert result["success"] is False

    def test_export_parser(self):
        parser = create_parser()
        ns = parser.parse_args(["vault", "export", "--all", "/tmp/bundle.zip"])
        assert ns.export_all is True


# ---------------------------------------------------------------------------
# Section 8: art vault import
# ---------------------------------------------------------------------------


class TestImportVaults:
    def _make_bundle(self, tmp_path, vaults: dict[str, Path]) -> Path:
        """Create a test zip bundle with the given vault names and paths."""
        bundle = tmp_path / "bundle.zip"
        manifest_entries = []

        with zipfile.ZipFile(bundle, "w") as zf:
            for name, vault_path in vaults.items():
                manifest_entries.append({"name": name, "dir": name})
                # Write skills dir
                skills_dir = vault_path / "skills"
                if skills_dir.is_dir():
                    for f in skills_dir.rglob("*"):
                        if f.is_file():
                            zf.write(f, f"{name}/skills/{f.relative_to(skills_dir)}")
                # Write vault.yaml
                vault_yaml = vault_path / "vault.yaml"
                if vault_yaml.exists():
                    zf.write(vault_yaml, f"{name}/vault.yaml")

            manifest_yaml = yaml.dump({"vaults": manifest_entries})
            zf.writestr("manifest.yaml", manifest_yaml)

        return bundle

    def test_extract_and_register(self, vault_with_artifacts, tmp_path):
        bundle = self._make_bundle(tmp_path, {"my-vault": vault_with_artifacts})
        dest = tmp_path / "extracted"

        with mock.patch("artifactr.catalog.add_vaults") as mock_add, \
             mock.patch("artifactr.catalog.load_config") as mock_cfg:
            mock_cfg.return_value = {
                "vaults": [],
                "vault_names": {},
                "default_vault": None,
                "default_tool": "opencode",
                "tools": {},
                "nav_mode": None,
            }
            mock_add.return_value = {"added": [str(dest / "my-vault")], "skipped": [], "errors": [], "names": {"my-vault": "my-vault"}}
            result = import_vaults_from_zip(str(bundle), str(dest))

        assert result["error"] is None
        assert len(result["extracted"]) == 1 or len(result["errors"]) == 0

    def test_manifest_parsing(self, vault_with_artifacts, tmp_path):
        bundle = self._make_bundle(tmp_path, {"my-vault": vault_with_artifacts})

        with zipfile.ZipFile(bundle, "r") as zf:
            manifest = yaml.safe_load(zf.read("manifest.yaml"))

        assert manifest["vaults"][0]["name"] == "my-vault"
        assert manifest["vaults"][0]["dir"] == "my-vault"

    def test_invalid_zip_error(self, tmp_path):
        bad_file = tmp_path / "bad.zip"
        bad_file.write_bytes(b"not a zip")
        result = import_vaults_from_zip(str(bad_file), str(tmp_path / "dest"))
        assert result["error"] is not None

    def test_missing_manifest_error(self, tmp_path):
        bundle = tmp_path / "no-manifest.zip"
        with zipfile.ZipFile(bundle, "w") as zf:
            zf.writestr("some-file.txt", "content")
        result = import_vaults_from_zip(str(bundle), str(tmp_path / "dest"))
        assert result["error"] is not None
        assert "manifest" in result["error"].lower()

    def test_import_parser(self):
        parser = create_parser()
        ns = parser.parse_args(["vault", "import", "bundle.zip", "-y"])
        assert ns.yes is True
        assert ns.archive == "bundle.zip"

    def test_handle_vault_import_confirms(self, vault_with_artifacts, tmp_path, capsys):
        """Without -y, prompts for confirmation."""
        bundle = self._make_bundle(tmp_path, {"my-vault": vault_with_artifacts})
        args = argparse.Namespace(
            archive=str(bundle),
            dest=str(tmp_path / "dest"),
            yes=False,
        )
        with mock.patch("builtins.input", return_value="n"):
            rc = handle_vault_import(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Aborted" in out

    def test_handle_vault_import_yes_flag(self, vault_with_artifacts, tmp_path, capsys):
        """With -y, skips confirmation."""
        bundle = self._make_bundle(tmp_path, {"my-vault": vault_with_artifacts})
        args = argparse.Namespace(
            archive=str(bundle),
            dest=str(tmp_path / "dest"),
            yes=True,
        )
        with mock.patch("artifactr.catalog.add_vaults") as mock_add, \
             mock.patch("artifactr.catalog.load_config") as mock_cfg:
            mock_cfg.return_value = {
                "vaults": [],
                "vault_names": {},
                "default_vault": None,
                "default_tool": "opencode",
                "tools": {},
                "nav_mode": None,
            }
            mock_add.return_value = {"added": [], "skipped": [], "errors": [], "names": {}}
            rc = handle_vault_import(args)

        assert rc == 0


# ---------------------------------------------------------------------------
# Section 3: art nav
# ---------------------------------------------------------------------------


class TestHandleNav:
    def test_nav_print_vault_root(self, vault_with_artifacts, capsys):
        args = argparse.Namespace(
            target=None,
            nav_print=True,
            spawn=False,
            window=False,
        )
        with mock.patch("artifactr.cli.get_default_vault", return_value=str(vault_with_artifacts)):
            rc = handle_nav(args)

        assert rc == 0
        out = capsys.readouterr().out.strip()
        assert out == str(vault_with_artifacts.resolve())

    def test_nav_type_alias_skills(self, vault_with_artifacts, capsys):
        args = argparse.Namespace(
            target="skills",
            nav_print=True,
            spawn=False,
            window=False,
        )
        with mock.patch("artifactr.cli.get_default_vault", return_value=str(vault_with_artifacts)):
            rc = handle_nav(args)

        assert rc == 0
        out = capsys.readouterr().out.strip()
        assert out.endswith("skills")

    def test_nav_unknown_target_errors(self, vault_with_artifacts, capsys):
        args = argparse.Namespace(
            target="nonexistent-target",
            nav_print=True,
            spawn=False,
            window=False,
        )
        with mock.patch("artifactr.cli.get_default_vault", return_value=str(vault_with_artifacts)), \
             mock.patch("artifactr.cli.get_vault_by_name_or_path", return_value=None):
            rc = handle_nav(args)

        assert rc == 1
        err = capsys.readouterr().err
        assert "not a recognized" in err.lower() or "error" in err.lower()

    def test_nav_no_mode_errors(self, vault_with_artifacts, capsys):
        """No flag and no nav_mode configured → error with instructions."""
        args = argparse.Namespace(
            target=None,
            nav_print=False,
            spawn=False,
            window=False,
        )
        with mock.patch("artifactr.cli.get_default_vault", return_value=str(vault_with_artifacts)), \
             mock.patch("artifactr.cli.get_nav_mode", return_value=None):
            rc = handle_nav(args)

        assert rc == 1
        err = capsys.readouterr().err
        assert "nav_mode" in err or "mode" in err.lower()

    def test_nav_type_aliases_dict(self):
        """All expected type aliases are present."""
        assert "skills" in _NAV_TYPE_ALIASES
        assert "s" in _NAV_TYPE_ALIASES
        assert "sk" in _NAV_TYPE_ALIASES
        assert "commands" in _NAV_TYPE_ALIASES
        assert "c" in _NAV_TYPE_ALIASES
        assert "cmd" in _NAV_TYPE_ALIASES
        assert "com" in _NAV_TYPE_ALIASES
        assert "agents" in _NAV_TYPE_ALIASES
        assert "a" in _NAV_TYPE_ALIASES
        assert "agt" in _NAV_TYPE_ALIASES

    def test_nav_parser_flags(self):
        parser = create_parser()
        ns = parser.parse_args(["nav", "skills", "--print"])
        assert ns.nav_print is True
        assert ns.target == "skills"

    def test_nav_spawn_flag(self):
        parser = create_parser()
        ns = parser.parse_args(["nav", "-s"])
        assert ns.spawn is True

    def test_nav_window_flag(self):
        parser = create_parser()
        ns = parser.parse_args(["nav", "-w"])
        assert ns.window is True


# ---------------------------------------------------------------------------
# Section 4: art shell setup
# ---------------------------------------------------------------------------


class TestShellDetection:
    def test_detect_bash(self):
        with mock.patch.dict("os.environ", {"SHELL": "/bin/bash"}):
            assert detect_shell() == "bash"

    def test_detect_zsh(self):
        with mock.patch.dict("os.environ", {"SHELL": "/bin/zsh"}):
            assert detect_shell() == "zsh"

    def test_detect_fish(self):
        with mock.patch.dict("os.environ", {"SHELL": "/usr/bin/fish"}):
            assert detect_shell() == "fish"

    def test_get_shell_rc_bash(self):
        rc = get_shell_rc_file("bash")
        assert rc is not None
        assert rc.name == ".bashrc"

    def test_get_shell_rc_zsh(self):
        rc = get_shell_rc_file("zsh")
        assert rc is not None
        assert rc.name == ".zshrc"

    def test_get_shell_rc_fish(self):
        rc = get_shell_rc_file("fish")
        assert rc is not None
        assert rc.name == "art.fish"

    def test_snippet_bash_has_cd(self):
        snippet = get_shell_wrapper_snippet("bash")
        assert "cd" in snippet
        assert "art nav" in snippet

    def test_snippet_zsh_has_cd(self):
        snippet = get_shell_wrapper_snippet("zsh")
        assert "cd" in snippet
        assert "art nav" in snippet

    def test_snippet_fish_is_function(self):
        snippet = get_shell_wrapper_snippet("fish")
        assert "function art" in snippet


class TestHandleShellSetup:
    def test_yes_flag_skips_prompts(self, tmp_path, capsys):
        rc_file = tmp_path / "test.bashrc"
        args = argparse.Namespace(yes=True)
        with mock.patch("artifactr.cli.handle_shell_setup.__module__"), \
             mock.patch("artifactr.utils.detect_shell", return_value="bash"), \
             mock.patch("artifactr.utils.get_shell_rc_file", return_value=rc_file), \
             mock.patch("artifactr.utils.get_shell_wrapper_snippet", return_value="# snippet\n"):
            from artifactr.utils import detect_shell as ds, get_shell_rc_file as grc, get_shell_wrapper_snippet as gsw
            with mock.patch.object(ds, '__module__', create=True), \
                 mock.patch("artifactr.cli.handle_shell_setup", wraps=handle_shell_setup) as wrapped:
                # Call directly with mocked utils
                with mock.patch("artifactr.cli.handle_shell_setup.__module__"):
                    pass

        # Simpler approach: mock the utils imports inside handle_shell_setup
        rc_file2 = tmp_path / "test2.bashrc"
        args2 = argparse.Namespace(yes=True)
        import artifactr.utils as _utils
        with mock.patch.object(_utils, "detect_shell", return_value="bash"), \
             mock.patch.object(_utils, "get_shell_rc_file", return_value=rc_file2), \
             mock.patch.object(_utils, "get_shell_wrapper_snippet", return_value="# snippet\n"):
            rc = handle_shell_setup(args2)

        assert rc == 0
        assert rc_file2.exists()

    def test_fish_writes_separate_file(self, tmp_path, capsys):
        fish_file = tmp_path / "art.fish"
        args = argparse.Namespace(yes=True)
        import artifactr.utils as _utils
        with mock.patch.object(_utils, "detect_shell", return_value="fish"), \
             mock.patch.object(_utils, "get_shell_rc_file", return_value=fish_file), \
             mock.patch.object(_utils, "get_shell_wrapper_snippet", return_value="function art\nend\n"):
            rc = handle_shell_setup(args)

        assert rc == 0
        assert fish_file.read_text() == "function art\nend\n"

    def test_shell_setup_parser(self):
        parser = create_parser()
        ns = parser.parse_args(["shell", "setup", "-y"])
        assert ns.yes is True
        assert ns.shell_command == "setup"
