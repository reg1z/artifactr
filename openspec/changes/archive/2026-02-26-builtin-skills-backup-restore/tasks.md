## 1. Version Bump

- [x] 1.1 Update `version` in `pyproject.toml` from `0.4.0` to `0.4.1`
- [x] 1.2 Update the `--version` output string in `cli.py` to `0.4.1`
- [x] 1.3 Fix stale version assertion in `tests/test_project_structure.py` from `"0.3.3"` to `"0.4.1"`
- [x] 1.4 Remove the "known failing test" note from `AGENTS.md`

## 2. Package Data Setup

- [x] 2.1 Add `[tool.setuptools.package-data]` stanza to `pyproject.toml` with `"artifactr" = ["builtin_skills/**/*"]`
- [x] 2.2 Create the `src/artifactr/builtin_skills/` directory with `skills/` and `commands/` subdirectories

## 3. Built-in Skill Files

- [x] 3.1 Write `src/artifactr/builtin_skills/skills/artifactr-context/artifact.md` — covers: what Artifactr is; config file location (`~/.config/artifactr/config.yaml`); all config.yaml fields; vault structure; `vault.yaml` format; artifact types and file formats; how to find the default vault; three-tier tool resolution. Include `version: 0.1` in frontmatter.
- [x] 3.2 Write `src/artifactr/builtin_skills/skills/art-create-skill/artifact.md` — covers creating skills with `art create skill/<name>`, slash syntax, relevant flags. Include `version: 0.1` in frontmatter.
- [x] 3.3 Write `src/artifactr/builtin_skills/skills/art-create-cmd/artifact.md` — covers creating commands with `art create command/<name>`. Include `version: 0.1` in frontmatter.
- [x] 3.4 Write `src/artifactr/builtin_skills/skills/art-create-agent/artifact.md` — covers creating agents with `art create agent/<name>`. Include `version: 0.1` in frontmatter.
- [x] 3.5 Write `src/artifactr/builtin_skills/commands/art-create-skill.md` — token-minimal paired command (essential `art create skill/<name>` invocation with minimal framing)
- [x] 3.6 Write `src/artifactr/builtin_skills/commands/art-create-cmd.md` — token-minimal paired command
- [x] 3.7 Write `src/artifactr/builtin_skills/commands/art-create-agent.md` — token-minimal paired command

## 4. builtins.py Module

- [x] 4.1 Create `src/artifactr/builtins.py` with `get_builtin_skills_root() -> Traversable` using `importlib.resources.files("artifactr") / "builtin_skills"`
- [x] 4.2 Implement `install_builtin_skills(target_skills_dir: Path, target_commands_dir: Path | None) -> dict` — copies skill directories from `builtin_skills/skills/` and command files from `builtin_skills/commands/`, silently overwriting existing files. Returns `{"skills_installed": int, "commands_installed": int}`.

## 5. `art update-native-skills` Command

- [x] 5.1 Register `update-native-skills` parser (alias `uns`) under top-level subparsers in `cli.py` with `make_help(...)`, `-g`/`--global` flag, and `--tools` flag
- [x] 5.2 Implement `handle_update_native_skills(args) -> int` in `cli.py`:
  - Resolve target tool(s) from `--tools` or default tool
  - If not `--global` and CWD is not a git repo: prompt Y/n, abort on `n`
  - For each tool, resolve skills dir and commands dir (local or global depending on `-g`)
  - Call `install_builtin_skills()` for each tool
  - Print summary of installed counts
- [x] 5.3 Wire `handle_update_native_skills` into the main dispatch in `cli.py`
- [x] 5.4 Write tests for `art update-native-skills` covering: local install, global install (`-g`), `--tools` override, git-repo confirmation prompt (non-git CWD), abort on `n`, silent overwrite

## 6. Backup Business Logic

- [x] 6.1 Implement `backup_catalog(output_path: str) -> dict` in `catalog.py`:
  - Resolve all registered vaults
  - Build zip using `export_vaults()` pattern (vault dirs named by vault name)
  - Append `config_snapshot.yaml` entry with `format_version`, `created_at`, `default_vault_name` (name, not path), `default_tool`, `nav_mode`, `tools`
  - Error if output already exists
  - Return `{"success": bool, "output": str | None, "vault_count": int, "error": str | None}`

## 7. Restore Business Logic

- [x] 7.1 Implement `restore_catalog(archive_path: str) -> dict` in `catalog.py`:
  - Validate zip and presence of `manifest.yaml` and `config_snapshot.yaml`
  - Extract each vault to `~/.config/artifactr/vaults/<vault-name>/`, resolving name conflicts by appending `-1`, `-2`, etc.
  - Register each extracted vault via `add_vaults()`
  - Apply `default_tool`, `nav_mode`, `tools` from snapshot to `config.yaml`
  - Set `default_vault` to the extracted path of the vault matching `default_vault_name`; warn if not found
  - Return `{"success": bool, "extracted": list[dict], "renames": dict, "errors": list[str], "error": str | None}`

## 8. `art config backup` and `art config restore` Commands

- [x] 8.1 Register `backup` parser under `conf_subparsers` in `cli.py` with optional positional `output` argument and `make_help(...)`
- [x] 8.2 Implement `handle_config_backup(args) -> int` — calls `backup_catalog()`, prints output path on success
- [x] 8.3 Register `restore` parser under `conf_subparsers` in `cli.py` with required positional `archive` argument and `make_help(...)`
- [x] 8.4 Implement `handle_config_restore(args) -> int` — calls `restore_catalog()`, prints extracted vaults, reports any renames or warnings
- [x] 8.5 Wire both handlers into the `conf_command` dispatch block in `cli.py`
- [x] 8.6 Write tests for `art config backup` covering: default filename, custom output path, errors on existing output, all-vaults included, config snapshot content
- [x] 8.7 Write tests for `art config restore` covering: valid archive restore, extraction location, name conflict rename, config settings applied, default vault set, missing archive error, missing manifest error, missing `default_vault_name` warning
