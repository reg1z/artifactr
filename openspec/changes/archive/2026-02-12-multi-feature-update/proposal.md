## Why

The CLI is missing several vault management, artifact creation, and artifact editing capabilities outlined in the project roadmap. Users cannot initialize new vaults from scratch, cannot create command or agent artifacts (only skills), cannot edit artifacts in-place, and must always type `claude-code` instead of the shorter `claude`. These gaps make the tool less ergonomic and incomplete relative to the artifact types it already supports for import/discovery/store.

## What Changes

- **`art vault add` auto-naming**: Vaults added without `--name` are automatically assigned a name using the pattern `llm-vault-1`, `llm-vault-2`, etc. Name collisions on explicit `--name` produce an error with actionable guidance. A new `--set-default` flag allows setting the vault as default at add time.
- **`art vault init` command**: New command to create a vault directory from scratch (scaffolding `skills/`, `agents/`, `commands/` subdirectories), register it, and optionally name/set-default. Idempotent: if the directory already exists, it behaves like `vault add`.
- **`art edit` command**: Opens an artifact's main `.md` file in the user's terminal editor (`$VISUAL` -> `$EDITOR` -> `nano` -> `nvim` -> `vim` -> `vi`). Supports vault-based and project-local (`--here`) editing.
- **Generalized `art create` for commands and agents**: Extends the existing skill creation to support `art create command <name>` and `art create agent <name>`, both requiring `--description`. Commands are flat files where the filename is the command name (no `name` frontmatter). Agents are flat files with `name` in frontmatter. The underlying `creator.py` is generalized to handle all artifact types.
- **Tool alias support**: `claude` is accepted as an alias for `claude-code` everywhere a tool name is used (`--tools`, `art tool select`, etc.). `art tool list` displays aliases.

## Capabilities

### New Capabilities
- `vault-init`: Vault initialization from scratch with directory scaffolding and automatic registration
- `artifact-editing`: Opening artifact files in the user's terminal editor for in-place editing
- `tool-aliases`: Alias resolution layer for tool names (e.g., `claude` -> `claude-code`)

### Modified Capabilities
- `vaults`: Auto-naming on add (`llm-vault-N`), `--set-default` flag, improved error messages mentioning `vault init`
- `creation`: Generalized artifact creation supporting commands and agents in addition to skills
- `cli`: New subcommands (`vault init`, `edit`, `create command`, `create agent`), tool alias display in `tool list`
- `importing`: Tool alias resolution in `--tools` validation
- `core`: Tool alias map and resolution function in the tools registry

## Impact

- **Files modified**: `catalog.py`, `creator.py`, `cli.py`, `tools/__init__.py`, `importer.py`, `utils.py`
- **Files added**: None anticipated (all changes fit existing modules)
- **Tests**: New tests for vault init, artifact creation (command/agent), editing, tool aliases. Modified tests for vault add auto-naming.
- **Dependencies**: No new dependencies. Editor launching uses `subprocess` and `shutil.which` (stdlib).
- **Breaking changes**: None. All existing behavior is preserved; new features are additive.
