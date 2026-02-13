## Context

The extensible tool system has three-tier resolution (builtins < global config < vault) fully implemented in `tools/__init__.py` via `_build_tool_registry(extra_tools, vault_tools)`. However, the CLI handler functions (`handle_tool_list`, `handle_tool_show`, `handle_tool_select`) only ever call `load_global_tools()` and never pass `vault_tools`, making vault-defined tools invisible. The write path (`tool add --vault`, `tool rm --vault`) works correctly.

Additionally, `art tool show` currently does a single-tool deep dive but there's no way to see a comprehensive catalog of all tools across all vaults. The command is being split: `art tool list` for active/resolved tools, `art tool info` for the full catalog.

## Goals / Non-Goals

**Goals:**
- `art tool list` shows resolved tools using three-tier resolution with the default vault
- `art tool list --vault=X` shows resolution using a specific vault instead of the default
- `art tool select` can select vault-defined tools and aliases
- `art tool info` (no args) shows all tools grouped by source across all registered vaults, plus CWD `vault.yaml` if present
- `art tool info <name>` shows detailed info for a single tool
- `load_active_vault_tools()` helper centralizes default vault tool loading

**Non-Goals:**
- CWD `vault.yaml` does not participate in tool resolution (informational only in `art tool info`)
- No changes to `art tool add` or `art tool rm` behavior
- No changes to import-time tool resolution (already works correctly with vault_tools param)

## Decisions

### 1. `load_active_vault_tools()` helper in `config.py`

**Decision**: Add a helper function that loads tools from the default vault and returns `(tools_dict, vault_name)`.

**Rationale**: All three CLI handlers need the same "get me the default vault's tools" logic. Centralizing it avoids repetition and ensures consistency. Placed in `config.py` alongside the existing `load_global_tools()`.

**Alternative considered**: Putting it in `tools/__init__.py`. Rejected because it depends on vault catalog operations (`get_default_vault`, `load_vault_metadata`) which live in `config.py`/`catalog.py`.

### 2. `art tool list --vault` flag replaces default vault in resolution

**Decision**: When `--vault=X` is provided, it replaces the default vault in three-tier resolution (builtins + global + X). It does not add X alongside the default vault.

**Rationale**: Simulating "what would I see if this were my default vault" is the most useful mental model. Combining multiple vaults would create confusing precedence questions.

### 3. Rename `show` → `info` and expand scope

**Decision**: Rename the subcommand from `show` to `info`. Without args, it becomes a comprehensive catalog view grouped by source. With a name arg, it keeps the existing deep-dive behavior.

**Rationale**: `list` and `show` are too similar in meaning. `info` clearly suggests "information about" rather than "display items". The no-args mode fills a gap — there's currently no way to see what tools are available across all vaults before selecting one.

### 4. CWD `vault.yaml` detection for `art tool info` only

**Decision**: `art tool info` checks for `./vault.yaml` in the current working directory. If found, its tools are displayed in a separate "CURRENT DIRECTORY" section. This is purely informational — CWD tools do not affect resolution in `list` or `select`.

**Rationale**: Users working inside a vault directory should be able to see what tools that vault provides. But mixing CWD detection into resolution would create unpredictable behavior depending on where you run the command.

### 5. `load_all_vault_tools()` helper for catalog view

**Decision**: Add a function that iterates all registered vaults and returns a list of `(vault_name, vault_path, tools_dict)` tuples. Used by `art tool info`.

**Rationale**: The catalog view needs per-vault grouping, not merged resolution. A separate function keeps this distinct from the resolution-oriented `load_active_vault_tools()`.

### 6. `art tool info <name>` shows all definitions, not just the resolved one

**Decision**: When a tool name is provided, show every definition of that tool across all tiers (built-in, global config, each vault, CWD), with the currently active/resolved one marked with `✓ ACTIVE`. Overridden definitions are marked `○` with `(overridden)`.

**Rationale**: A user needs to understand *why* a tool resolves a certain way. If `my-tool` exists in both global config and a vault, showing only the resolved one hides the override. Showing all definitions makes the precedence system transparent and debuggable.

**Alternative considered**: Show only the resolved definition. Rejected because it makes overrides invisible and hard to debug.

### 7. `--vault` and `--global` filtering flags on `art tool info`

**Decision**: `art tool info` accepts `--vault` (with optional value) and `--global` flags that filter both catalog and detail views:
- `--vault=X`: filter to vault X's tools (by name or path)
- `--vault` (no value): filter to default vault's tools
- `--global`: filter to global config tools only

These flags work in both modes (no-args catalog view and `<name>` detail view). When used with a name, only that source's definition is shown.

**Rationale**: Users need targeted inspection. "What tools does this vault provide?" and "What's the global config's version of this tool?" are natural questions. Using `nargs='?'` for `--vault` gives three states: absent, present without value (default vault), present with value (specific vault).

## Risks / Trade-offs

- **[Risk] CWD vault.yaml may not be a registered vault** → This is fine; `info` is informational. Clearly label as "CURRENT DIRECTORY (./vault.yaml)" so users understand it's not part of active resolution.
- **[Risk] `art tool show` rename is a breaking change** → Minor impact since the tool system is new. No known external consumers.
- **[Trade-off] `art tool info` with no args iterates all vaults** → Could be slow with many vaults. Acceptable for now; this is not a hot path.
