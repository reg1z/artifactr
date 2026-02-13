## 1. Shared Infrastructure

- [x] 1.1 Add `add_type_filter_args(parser, allow_names=True)` helper to `cli.py` that registers `-S`/`--skills`, `-C`/`--commands`, `-A`/`--agents` flags with `nargs='?'` (when `allow_names=True`) or `store_true` (when `allow_names=False`)
- [x] 1.2 Add `resolve_type_filters(args)` helper to `cli.py` that returns `None` (no filters) or a dict mapping type names to `True` or list of names
- [x] 1.3 Add `get_tool_global_dirs()` function to `tools/__init__.py` that returns a mapping of tool name to dict of artifact_type -> global path (analogous to `get_tool_config_dirs` but for global paths)
- [x] 1.4 Add vault detection helper: function that checks if a directory contains `vault.yaml` and returns whether it should be treated as a vault
- [x] 1.5 Add cache cleanup utilities to `importer.py`: `remove_from_import_cache(target, artifact_names)` and `remove_from_global_import_cache(artifact_names)` for removing entries from `.art-cache/imported` and `.art-cache-global/imported`
- [x] 1.6 Add `discover_vault_artifacts(vault_path)` to `scanner.py` that scans a vault's `skills/`, `commands/`, `agents/` directories directly (without tool config dirs)
- [x] 1.7 Add `discover_global_artifacts(tools_filter=None)` to `scanner.py` that scans global config directories for artifacts using tool global paths

## 2. Top-level Commands: `art list` and `art rm`

- [x] 2.1 Add `art list` subparser to `create_parser()` with `--vault` and type filter flags (via `add_type_filter_args`)
- [x] 2.2 Implement `handle_list(args)` handler: resolve vault, scan vault artifacts, apply type filters, display table with NAME, TYPE, DESCRIPTION columns using `extract_description`
- [x] 2.3 Add `art rm` subparser to `create_parser()` with positional `names` (`nargs='+'`), `--vault`, and `-f`/`--force`
- [x] 2.4 Implement `handle_rm(args)` handler: resolve vault, resolve artifact names (with disambiguation), show confirmation, delete artifacts from vault directory

## 3. Project Namespace (`art project` / `art proj`)

- [x] 3.1 Register `project` subparser with alias `proj` and nested subparsers for `import`, `rm`, `wipe`, `list`
- [x] 3.2 Add `proj import` subparser: optional positional `target` (`nargs='?'`, defaults to cwd), `--vault`, `--tools`, `--artifacts`, `-l`/`--link`, `-f`/`--force`, `--no-exclude`, and type filter flags
- [x] 3.3 Implement `handle_proj_import(args)` handler: adapt existing `handle_import` logic to use cwd default, support `--no-exclude` (skip exclude patterns but still add `.art-cache`), integrate type filters
- [x] 3.4 Refactor `import_artifacts()` in `importer.py`: add `no_exclude` parameter and `type_filters` parameter to support the new flags
- [x] 3.5 Add `proj rm` subparser: positional `names` (`nargs='+'`), `--target` (optional, defaults to cwd), `--tools`, `-f`/`--force`, and type filter flags (`store_true` via `allow_names=False`)
- [x] 3.6 Implement `handle_proj_rm(args)` handler: locate artifacts in project using tool config dirs and cache, confirm, delete files, update `.art-cache/imported`
- [x] 3.7 Add `proj wipe` subparser: `--target` (optional, defaults to cwd), `--tools`, `-f`/`--force`, and type filter flags (`nargs='?'`)
- [x] 3.8 Implement `handle_proj_wipe(args)` handler: read `.art-cache/imported`, resolve artifact locations, apply type/tool filters, confirm, delete files, clear cache entries
- [x] 3.9 Add `proj list` subparser: `--target` (optional, defaults to cwd), `--tools`, and type filter flags (`nargs='?'`)
- [x] 3.10 Implement `handle_proj_list(args)` handler: read `.art-cache/imported`, apply type/tool filters, display table

## 4. Config Namespace (`art config` / `art conf`)

- [x] 4.1 Register `config` subparser with alias `conf` and nested subparsers for `import`, `rm`, `wipe`, `list`
- [x] 4.2 Add `conf import` subparser: `--vault`, `--tools`, `--artifacts`, `-l`/`--link`, `-f`/`--force`, and type filter flags
- [x] 4.3 Implement `handle_conf_import(args)` handler: adapt existing `import_artifacts_global` logic, integrate type filters
- [x] 4.4 Refactor `import_artifacts_global()` in `importer.py`: add `type_filters` parameter
- [x] 4.5 Add `conf rm` subparser: positional `names` (`nargs='+'`), `--tools`, `-f`/`--force`, and type filter flags (`store_true`)
- [x] 4.6 Implement `handle_conf_rm(args)` handler: locate artifacts in global dirs, confirm, delete, update `.art-cache-global/imported`
- [x] 4.7 Add `conf wipe` subparser: `--tools`, `-f`/`--force`, and type filter flags (`nargs='?'`)
- [x] 4.8 Implement `handle_conf_wipe(args)` handler: read `.art-cache-global/imported`, resolve locations, apply filters, confirm, delete, clear cache
- [x] 4.9 Add `conf list` subparser: `--tools`, and type filter flags (`nargs='?'`)
- [x] 4.10 Implement `handle_conf_list(args)` handler: read `.art-cache-global/imported`, apply filters, display table

## 5. Spelunk Enhancements

- [x] 5.1 Update `spelunk` subparser: make `target` optional (`nargs='?'`), add `-g`/`--global`, `--tools`, and type filter flags
- [x] 5.2 Update spelunk help text to clarify the command probes repos, vaults, or global configs
- [x] 5.3 Implement global config spelunk mode in `handle_spelunk`: when no target and no `-g`, print message that global config is being spelunked by default, then scan global dirs
- [x] 5.4 Implement vault detection in `handle_spelunk`: check for `vault.yaml`, dispatch to `discover_vault_artifacts` if found
- [x] 5.5 Integrate `--tools` filter into spelunk: filter which tools' dirs are scanned
- [x] 5.6 Integrate type filter flags into spelunk: filter discovered artifacts by type

## 6. Store Enhancements

- [x] 6.1 Add type filter flags to `store` subparser
- [x] 6.2 Integrate type filters into `handle_store`: filter discovered artifacts before presenting selection

## 7. Remove Old Import Command

- [x] 7.1 Remove top-level `import` subparser from `create_parser()`
- [x] 7.2 Remove `handle_import(args)` handler and its routing in `main()`
- [x] 7.3 Remove the `--global`/`-g` flag logic from import (now handled by `conf import`)

## 8. CLI Routing

- [x] 8.1 Add routing in `main()` for `art list` command
- [x] 8.2 Add routing in `main()` for `art rm` command
- [x] 8.3 Add routing in `main()` for `project`/`proj` namespace and its subcommands
- [x] 8.4 Add routing in `main()` for `config`/`conf` namespace and its subcommands

## 9. Version and Documentation

- [x] 9.1 Bump version to `0.0.7` in `pyproject.toml` and `src/artifactr/__init__.py`
- [x] 9.2 Create `CHANGELOG.md` with v0.0.7 entry documenting all changes
- [x] 9.3 Update `README.md` with new command structure and examples
- [x] 9.4 Update `ROADMAP.md` to check off completed items and reflect new state

## 10. Tests

- [x] 10.1 Add tests for `add_type_filter_args` and `resolve_type_filters` helpers
- [x] 10.2 Add tests for `art list` command
- [x] 10.3 Add tests for `art rm` command
- [x] 10.4 Add tests for `art proj import` (including cwd default, `--no-exclude`, type filters)
- [x] 10.5 Add tests for `art proj rm` (including cache cleanup)
- [x] 10.6 Add tests for `art proj wipe` (including type/tool filters, confirmation)
- [x] 10.7 Add tests for `art proj list`
- [x] 10.8 Add tests for `art conf import` (including type filters)
- [x] 10.9 Add tests for `art conf rm`
- [x] 10.10 Add tests for `art conf wipe`
- [x] 10.11 Add tests for `art conf list`
- [x] 10.12 Add tests for enhanced `art spelunk` (global default, vault detection, tool filter, type filters)
- [x] 10.13 Add tests for `art store` with type filters
- [x] 10.14 Verify old `art import` command is removed (parser does not accept it)
