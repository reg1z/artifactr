## Why

Artifactr has no built-in mechanism for giving coding agents context about itself, and no way to back up or restore vault catalogs — two gaps that limit usability for power users and teams adopting the tool. This release adds both, along with a version bump to 0.4.1.

## What Changes

- **New command `art update-native-skills` (alias `art uns`)**: Installs built-in skill and command files — bundled inside the Python package — into the current project or global tool config directories. Works from any PyPI install.
- **New built-in skill files**: Four skills (`artifactr-context`, `art-create-skill`, `art-create-cmd`, `art-create-agent`) and three paired token-optimal commands, embedded in the package under `src/artifactr/builtin_skills/`.
- **New command `art config backup [output.zip]`**: Zips all registered vault contents plus a configuration snapshot (default_tool, nav_mode, tools, default_vault_name) into a portable archive.
- **New command `art config restore <backup.zip>`**: Extracts and re-registers all vaults from a backup archive, restoring config settings. Vaults are always extracted to `~/.config/artifactr/vaults/`; absolute paths from the original machine are never restored.
- **Version bump**: 0.4.0 → 0.4.1.

## Capabilities

### New Capabilities

- `builtin-skills`: Package-embedded skill and command files that give coding agents context about Artifactr; the `art update-native-skills` command that installs them locally or globally.
- `config-backup-restore`: Full-catalog backup via `art config backup` and catalog restore via `art config restore`, including vault contents and config settings.

### Modified Capabilities

- `config-commands`: Two new subcommands (`backup`, `restore`) added to the `art config` namespace.

## Impact

- `pyproject.toml`: Add `[tool.setuptools.package-data]` stanza to include `builtin_skills/**/*`.
- `src/artifactr/builtins.py`: New module for resolving and copying built-in skill files via `importlib.resources`.
- `src/artifactr/builtin_skills/`: New directory tree of skill and command markdown files (package data).
- `src/artifactr/catalog.py`: New `backup_catalog()` and `restore_catalog()` functions (reuses `export_vaults()` logic).
- `src/artifactr/cli.py`: New `handle_update_native_skills()`, `handle_config_backup()`, `handle_config_restore()` handlers; new parser registrations.
- `tests/`: New test files for `update-native-skills`, `config backup`, and `config restore`.
- `tests/test_project_structure.py`: Update stale version assertion from `"0.3.3"` to `"0.4.1"`.
- `AGENTS.md`: Remove "known failing test" note after version assertion is fixed.
