## Why

The `install.sh` upgrade path is fragile — it detects "already up to date" by grepping pip output for "already satisfied", which fires on dependency lines and produces false negatives even after a successful upgrade. Users have no ergonomic way to update `art` without remembering the original one-liner install command.

## What Changes

- Add `art update` command (alias: `upgrade`) to the CLI
- Add `get_data_dir()` to `utils.py` for platform-appropriate data directory resolution (distinct from config dir on Linux)
- Add `src/artifactr/updater.py` module encapsulating all update logic
- `handle_update()` handler in `cli.py` wired to the new parser

## Capabilities

### New Capabilities

- `self-update`: The `art update` / `art upgrade` command — detects install method via `sys.executable` inspection, checks PyPI for the latest version, reports available upgrade, confirms with the user, runs the upgrade, verifies the result, and optionally repairs PATH on venv installs.

### Modified Capabilities

_(none — install-script behavior is unchanged by this change)_

## Impact

- **New file**: `src/artifactr/updater.py`
- **Modified**: `src/artifactr/utils.py` — add `get_data_dir()` (Linux: `~/.local/share/artifactr/`, macOS/Windows: same as `get_config_dir()`)
- **Modified**: `src/artifactr/cli.py` — add `add_parser` for `update`/`upgrade`, add `handle_update()`
- **No new dependencies** — uses only stdlib (`urllib.request`, `importlib.metadata`, `subprocess`, `json`, `sys`)
