## 1. Multi-vault infrastructure

- [x] 1.1 Add `_resolve_vault_paths()` helper that returns `list[Path]` from repeatable/comma-separated `-V` flags
- [x] 1.2 Update `art proj import` argparse to use `action="append"` for `-V` and update handler to loop over resolved vault paths
- [x] 1.3 Update `art conf import` argparse to use `action="append"` for `-V` and update handler to loop over resolved vault paths
- [x] 1.4 Update `art ls` argparse to use `action="append"` for `-V` and update handler to aggregate results across vaults, adding VAULT column when multiple
- [x] 1.5 Update `art store` argparse to use `action="append"` for `-V` and update handler to store into each resolved vault
- [x] 1.6 Update `art create` argparse to use `action="append"` for `-V` and update handler to create in each resolved vault
- [x] 1.7 Update `art tool add` argparse to use `action="append"` for `-V` and update handler to add tool config to each resolved vault
- [x] 1.8 Update `art tool ls` argparse to use `action="append"` for `-V` and update handler to list from multiple vaults
- [x] 1.9 Update `art tool info` argparse to use `action="append"` for `-V` and update handler to show info from multiple vaults

## 2. Project/config command vault filters

- [x] 2.1 Add `-V` flag to `art proj ls` (repeatable/comma-separated) and filter cache entries by vault label
- [x] 2.2 Add `-V` flag to `art proj rm` (repeatable/comma-separated) and filter cache entries by vault label
- [x] 2.3 Add `-V` flag to `art proj wipe` (repeatable/comma-separated) and filter cache entries by vault label
- [x] 2.4 Add `-V` flag to `art conf ls` (repeatable/comma-separated) and filter cache entries by vault label
- [x] 2.5 Add `-V` flag to `art conf rm` (repeatable/comma-separated) and filter cache entries by vault label
- [x] 2.6 Add `-V` flag to `art conf wipe` (repeatable/comma-separated) and filter cache entries by vault label

## 3. Tool discovery flags

- [x] 3.1 Add `-a`/`--all` flag to `art tool ls` — list tools from all catalog vaults + global config
- [x] 3.2 Add `-a`/`--all` flag to `art tool info` — show all tool definitions from all sources
- [x] 3.3 Add mutual exclusion validation between `--all` and `-V` for tool ls and tool info

## 4. Link state display

- [x] 4.1 Update `_load_cache_entries()` to preserve and return `link_state` field instead of stripping suffix
- [x] 4.2 Update `_load_global_cache_entries()` to preserve and return `link_state` field instead of stripping suffix
- [x] 4.3 Update `handle_proj_list()` to display STATE column and arrow indicators (→ linked, ⇒ hardlinked)
- [x] 4.4 Update `handle_conf_list()` to display STATE column and arrow indicators (→ linked, ⇒ hardlinked)
- [x] 4.5 Update `print_import_summary()` to accept link mode parameter and append `(linked)`/`(copied)` to output lines
- [x] 4.6 Pass link mode from import handlers to `print_import_summary()`

## 5. README update

- [x] 5.1 Document link/unlink commands (proj and conf) under Extended Usage
- [x] 5.2 Document `--link` import flag and link state output
- [x] 5.3 Document multi-vault `-V` syntax (comma-separated and repeatable) across commands
- [x] 5.4 Document `art tool ls --all` and `art tool info --all` flags
- [x] 5.5 Document link state display in `proj ls` / `conf ls` output
