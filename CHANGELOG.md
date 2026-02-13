# Changelog

## v0.0.7

### Breaking Changes
- **Removed `art import`**: Replaced by `art proj import` (project-side) and `art conf import` (global config-side).

### New Commands
- **`art list`**: List artifacts in a vault with NAME, TYPE, DESCRIPTION columns.
- **`art rm <names...>`**: Remove artifacts from a vault with interactive confirmation.
- **`art project` / `art proj`**: Project-side artifact operations.
  - `proj import [target]` — import artifacts into a project (defaults to cwd).
  - `proj rm <names...>` — remove imported artifacts from a project.
  - `proj wipe` — clear all imported artifacts from a project.
  - `proj list` — show imported artifacts via `.art-cache`.
- **`art config` / `art conf`**: Global config artifact operations.
  - `conf import` — import artifacts into global config directories.
  - `conf rm <names...>` — remove globally imported artifacts.
  - `conf wipe` — clear all globally imported artifacts.
  - `conf list` — show globally imported artifacts via `.art-cache-global`.

### New Features
- **Type filter flags**: `-S`/`--skills`, `-C`/`--commands`, `-A`/`--agents` available on most commands. Accepts optional comma-separated names (e.g., `-S foo,bar`).
- **`--no-exclude` on `proj import`**: Skip adding artifact paths to `.git/info/exclude` (`.art-cache` still excluded).
- **Enhanced `art spelunk`**:
  - Target is now optional — defaults to spelunking global config directories.
  - `-g`/`--global` flag for explicit global config scanning.
  - `--tools` flag to filter which tools' directories are scanned.
  - Vault detection via `vault.yaml` presence.
  - Type filter flags supported.
- **Type filters on `art store`**: Filter discovered artifacts by type before selection.

### Internal
- Added `add_type_filter_args()` and `resolve_type_filters()` shared helpers.
- Added `get_tool_global_dirs()` for global path resolution.
- Added `discover_vault_artifacts()` and `discover_global_artifacts()` to scanner.
- Added `remove_from_import_cache()` and `remove_from_global_import_cache()` cache cleanup utilities.
- Added `is_vault()` vault detection helper.
