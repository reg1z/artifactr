## 1. Helper Functions

- [x] 1.1 Add `load_active_vault_tools()` to `config.py` — returns `(tools_dict, vault_name)` from the default vault's `vault.yaml`, or `({}, None)` if no default vault
- [x] 1.2 Add `load_all_vault_tools()` to `config.py` — iterates all registered vaults, returns list of `(vault_name, vault_path, tools_dict)` tuples
- [x] 1.3 Add `load_cwd_vault_tools()` to `config.py` — reads `./vault.yaml` from current working directory, returns tools dict (empty if not present)

## 2. Vault-Aware Tool Resolution in CLI Handlers

- [x] 2.1 Update `handle_tool_list` to load default vault tools via `load_active_vault_tools()` and pass as `vault_tools=` to all tool resolution functions
- [x] 2.2 Add `--vault` flag to `art tool list` argparse registration; when provided, load that vault's tools instead of the default vault's
- [x] 2.3 Update `handle_tool_select` to load default vault tools and pass to `get_supported_tools()` and `resolve_tool_name()`

## 3. Rename `show` → `info` and Expand

- [x] 3.1 Rename argparse subcommand from `show` to `info`; make the positional `name` argument optional (with `nargs="?"`)
- [x] 3.2 Rename `handle_tool_show` to `handle_tool_info`; update dispatch in `main()`
- [x] 3.3 Implement no-args catalog view: grouped display of all tools by source (BUILT-IN, GLOBAL CONFIG, per-vault sections, CURRENT DIRECTORY)
- [x] 3.4 Implement CWD vault.yaml detection in the catalog view using `load_cwd_vault_tools()`
- [x] 3.5 Implement multi-definition detail view for `art tool info <name>`: show all definitions across all tiers with `✓ ACTIVE` / `○ (overridden)` / `○ (not active)` markers
- [x] 3.6 Add `--vault` flag to `art tool info` (`nargs="?"`, `const=True`): no value → default vault, with value → specific vault (by name or path)
- [x] 3.7 Add `--global` flag to `art tool info`: filter to global config tools only
- [x] 3.8 Implement filtering logic: `--vault` and `--global` filter both catalog view and detail view

## 4. Tests

- [x] 4.1 Test `load_active_vault_tools()` — default vault with tools, without tools, and no default vault
- [x] 4.2 Test `load_all_vault_tools()` — multiple vaults, empty catalog
- [x] 4.3 Test `load_cwd_vault_tools()` — vault.yaml present, absent, and missing tools section
- [x] 4.4 Test `handle_tool_list` includes vault-defined tools in output
- [x] 4.5 Test `handle_tool_list --vault=X` uses specified vault instead of default
- [x] 4.6 Test `handle_tool_select` can select a vault-defined tool
- [x] 4.7 Test `art tool info` no-args catalog view shows tools grouped by source
- [x] 4.8 Test `art tool info <name>` shows all definitions across tiers with active/overridden markers
- [x] 4.9 Test `art tool info --vault` (no value) filters to default vault
- [x] 4.10 Test `art tool info --vault=X` filters to specific vault (by name and by path)
- [x] 4.11 Test `art tool info --global` filters to global config tools
- [x] 4.12 Test `art tool info <name> --vault=X` shows only that vault's definition of the tool
- [x] 4.13 Test filter flags with no matching tools displays appropriate message
