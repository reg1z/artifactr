## Why

The `art tool` subcommands (`list`, `show`, `select`) only resolve tools from built-in defaults and the user's global config. They never load tool definitions from vault `vault.yaml` files, so vault-scoped tools are invisible to the CLI despite being writable via `art tool add --vault`. This makes the extensible tool system incomplete — users can add tools to vaults but can't see, select, or inspect them.

## What Changes

- **`art tool list`** loads tools from the default vault (three-tier resolution: builtins + global config + default vault). Supports `--vault` flag to target a specific vault instead of the default.
- **`art tool select`** resolves tools using the same three-tier resolution, so vault-defined tools and aliases can be selected.
- **Rename `art tool show` → `art tool info`**: Repurposed as a comprehensive catalog view.
  - `art tool info` (no args): Shows all tools grouped by source — built-in, global config, each registered vault, and CWD `vault.yaml` if present.
  - `art tool info <name>`: Deep dive on a single tool across all tiers.
- **CWD `vault.yaml` detection**: `art tool info` detects and displays tool definitions from a `vault.yaml` in the current working directory (informational only, does not affect resolution).
- **`load_active_vault_tools()` helper**: Centralized function to load the default vault's tools for use across CLI handlers.

## Capabilities

### New Capabilities
- `cwd-vault-detection`: Detecting and displaying tool definitions from a `vault.yaml` file in the current working directory

### Modified Capabilities
- `custom-tools`: Tool resolution in CLI handlers must include vault tools from the default vault; `art tool show` renamed to `art tool info` with expanded catalog behavior
- `cli`: New `art tool info` subcommand replaces `art tool show`; `art tool list` and `art tool select` gain vault-aware resolution; `art tool list` gains `--vault` flag

## Impact

- `src/artifactr/cli.py`: Handler functions `handle_tool_list`, `handle_tool_select`, `handle_tool_show` (renamed); argparse registration for `tool` subcommands
- `src/artifactr/config.py`: New `load_active_vault_tools()` helper function
- `src/artifactr/tools/__init__.py`: Possible additions to support iterating all vault tools for catalog view
- `tests/test_extensible_tools.py`: Tests for vault tool resolution in CLI handlers
