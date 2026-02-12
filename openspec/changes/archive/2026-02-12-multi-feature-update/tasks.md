## 1. Tool Alias Support

- [x] 1.1 Add `TOOL_ALIASES` dict and `resolve_tool_name()` function to `tools/__init__.py`
- [x] 1.2 Update `get_tool()` to resolve aliases before registry lookup
- [x] 1.3 Add `get_aliases_for_tool()` reverse lookup function to `tools/__init__.py`
- [x] 1.4 Update `importer.py` tool validation to resolve aliases before checking `supported_tools`
- [x] 1.5 Update `catalog.py` `select_default_tool()` to resolve aliases before validation
- [x] 1.6 Update `cli.py` `handle_tool_list` to display aliases in parentheses
- [x] 1.7 Add tests for alias resolution, alias-aware `get_tool()`, and reverse lookup

## 2. Vault Add Changes

- [x] 2.1 Add auto-naming logic to `catalog.py` `add_vaults()`: scan `vault_names` for `llm-vault-\d+`, assign next available
- [x] 2.2 Update `add_vaults()` to auto-name each added vault when no `--name` is provided
- [x] 2.3 Improve duplicate name error message to include the conflicting vault path and `art vault name` suggestion
- [x] 2.4 Add `--set-default` flag to `vault add` in `cli.py` and call `select_default()` when set
- [x] 2.5 Update `handle_vault_add` output to show assigned name, location, and rename hint for auto-named vaults
- [x] 2.6 Add tests for auto-naming (first vault, incrementing, multiple adds) and `--set-default`

## 3. Vault Init Command

- [x] 3.1 Add `init_vault()` function to `catalog.py`: create directory + scaffold subdirs + call `add_vaults()`
- [x] 3.2 Add `vault init` subcommand to `cli.py` with `target_dir` positional, `--name`, and `--set-default` flags
- [x] 3.3 Add `handle_vault_init` handler in `cli.py` that calls `init_vault()` and prints informative output
- [x] 3.4 Wire `vault init` into the `main()` dispatch
- [x] 3.5 Update "No default vault" error messages in `creator.py` and `importer.py` to mention `art vault init`
- [x] 3.6 Add tests for vault init (new dir, existing dir idempotent, with name, with set-default)

## 4. Generalized Artifact Creation

- [x] 4.1 Replace `create_skill()` with generalized `create_artifact()` in `creator.py` that branches on `artifact_type` (skill=directory, command/agent=file)
- [x] 4.2 Generalize `resolve_vault_target()` to accept `artifact_type` parameter and return correct path (dir for skills, `.md` file for commands/agents)
- [x] 4.3 Generalize `resolve_project_target()` to accept `artifact_type` parameter
- [x] 4.4 Add `create command` and `create agent` subcommands to `cli.py` with shared flag pattern
- [x] 4.5 Add `handle_create_artifact` generalized handler in `cli.py` (replaces `handle_create_skill`)
- [x] 4.6 Wire `create command` and `create agent` into `main()` dispatch
- [x] 4.7 Update existing `test_creator.py` tests for new `create_artifact()` signature
- [x] 4.8 Add tests for command creation (file-based, no name in frontmatter, description required)
- [x] 4.9 Add tests for agent creation (file-based, name in frontmatter, description required)

## 5. Artifact Editing

- [x] 5.1 Add `get_editor()` function to `utils.py`: `$VISUAL` -> `$EDITOR` -> `nano` -> `nvim` -> `vim` -> `vi` via `shutil.which()`
- [x] 5.2 Add `resolve_edit_target()` function to resolve artifact path for editing (vault mode and here mode)
- [x] 5.3 Add `art edit` command to `cli.py` with `artifact_type`, `artifact_name` positionals, `--vault`, `--here`, `--tools` flags
- [x] 5.4 Add `handle_edit` handler in `cli.py`: resolve target, get editor, `subprocess.run()`, return exit code
- [x] 5.5 Wire `edit` into `main()` dispatch
- [x] 5.6 Add tests for `get_editor()` (env vars, fallback chain, no editor found)
- [x] 5.7 Add tests for `resolve_edit_target()` (vault mode, here mode, not found)
