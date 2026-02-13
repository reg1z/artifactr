## Why

The CLI's command structure conflates vault-side and project-side operations under the same top-level namespace. As the tool grows, this makes the interface harder to reason about. Additionally, several common workflows are missing: listing vault contents, removing artifacts, managing globally imported artifacts, and filtering operations by artifact type. This release restructures the CLI into clear namespaces and adds the missing commands.

## What Changes

- **BREAKING**: `art import` removed. Replaced by `art proj import` (project-side) and `art conf import` (global config-side).
- **New namespace: `art project` / `art proj`**: Project-side operations with cwd-as-default.
  - `proj import [target]` — import artifacts from vault into a project (cwd default)
  - `proj rm <names...>` — remove imported artifacts from a project
  - `proj wipe` — clear all imported artifacts from a project
  - `proj list` — show what's been imported via .art-cache
- **New namespace: `art config` / `art conf`**: Global config operations.
  - `conf import` — import artifacts into global config directories
  - `conf rm <names...>` — remove globally imported artifacts
  - `conf wipe` — clear all globally imported artifacts
  - `conf list` — show globally imported artifacts via .art-cache-global
- **New command: `art list`** — list artifacts in a vault with descriptions and type filtering.
- **New command: `art rm`** — remove artifacts from a vault (interactive confirmation, `--force` to skip).
- **Type filter flags: `-S`/`--skills`, `-C`/`--commands`, `-A`/`--agents`** (uppercase short forms).
  - `nargs='?'` variant: accepts optional comma-separated names. Used on: `proj import`, `proj wipe`, `proj list`, `conf import`, `conf wipe`, `conf list`, `store`, `spelunk`, `art list`.
  - `store_true` variant: boolean-only filtering. Used on: `proj rm`, `conf rm`.
- **Spelunk changes**:
  - Target becomes optional; defaults to spelunking global config directories.
  - `-g`/`--global` flag for explicit global (redundant but clear).
  - `--tools` flag to filter to specific tool(s).
  - Vault detection via `vault.yaml` presence to probe vault artifact folders directly.
  - Help text clarifies the command probes repos, vaults, or global configs.
- **Import changes**:
  - `--no-exclude` flag on `proj import` to prevent adding artifacts to `.git/info/exclude` (`.art-cache` still excluded).
- **Version bump** to 0.0.7.
- **New `CHANGELOG.md`** — starts tracking from this version onwards.
- **Updated `README.md`** and **`ROADMAP.md`**.

## Capabilities

### New Capabilities
- `project-commands`: The `art proj`/`art project` subcommand namespace for project-side import, rm, wipe, and list operations with cwd-as-default behavior.
- `config-commands`: The `art conf`/`art config` subcommand namespace for global config import, rm, wipe, and list operations.
- `vault-artifact-listing`: The `art list` command for listing artifacts in a vault with descriptions and type filtering.
- `vault-artifact-removal`: The `art rm` command for removing artifacts from a vault with interactive confirmation.
- `type-filter-flags`: Shared `-S`/`-C`/`-A` type filter flags with `nargs='?'` and `store_true` variants, reusable across commands.

### Modified Capabilities
- `importing`: Import command moves to `proj import` and `conf import` namespaces. Adds `--no-exclude` flag on project import. Adds type filter flags. Project import target becomes optional (defaults to cwd).
- `discovery`: Spelunk target becomes optional (defaults to global configs). Adds vault detection via `vault.yaml`. Adds `--tools` and type filter flags. Adds `-g`/`--global` flag.
- `cli`: Top-level `art import` removed. New subcommand namespaces added (`project`/`proj`, `config`/`conf`). Argparse alias support for namespace names.

## Impact

- **CLI entry point** (`cli.py`): Major restructuring — new subparsers for `project`/`config` namespaces, removal of top-level `import`, new handlers for all new commands.
- **Importer** (`importer.py`): `--no-exclude` support, type-filter integration, cache cleanup utilities for rm/wipe.
- **Scanner** (`scanner.py`): Type filtering in `discover_artifacts`, vault detection logic, global config scanning.
- **Config** (`config.py`): No structural changes expected.
- **Tools** (`tools/__init__.py`, `tools/base.py`): Global path resolution for spelunk global mode.
- **New shared utilities**: `add_type_filter_args()`, `resolve_type_filters()` helper functions.
- **pyproject.toml** and `__init__.py`: Version bump.
- **Documentation**: CHANGELOG.md (new), README.md (updated), ROADMAP.md (updated).
