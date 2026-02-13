## 1. GenericToolAdapter and Built-in Tools Data

- [ ] 1.1 Create `BUILTIN_TOOLS` dict in `tools/__init__.py` with definitions for `claude-code`, `opencode`, and `codex` using the tool definition schema (aliases, per-artifact-type paths, global paths)
- [ ] 1.2 Implement `GenericToolAdapter` class in `tools/base.py` — constructor takes a tool name and config dict; exposes `name`, `supported_types`, `get_destination()`, `get_global_destination()` with `ValueError` for unsupported types; handles `$HOME`/`~` path expansion
- [ ] 1.3 Remove `ToolAdapter` ABC from `tools/base.py` (or repurpose as the `GenericToolAdapter` itself)
- [ ] 1.4 Remove `tools/claude_code.py` and `tools/opencode.py`
- [ ] 1.5 Update `tools/__init__.py`: remove `TOOL_REGISTRY` and `TOOL_ALIASES` dicts; replace with functions that build the tool registry from `BUILTIN_TOOLS` + config sources; update `get_tool()`, `resolve_tool_name()`, `get_supported_tools()`, `get_tool_config_dirs()`

## 2. Config Layer — Global Tools and vault.yaml

- [ ] 2.1 Update `config.py` to load/save `tools:` section from `~/.config/artifactr/config.yaml`
- [ ] 2.2 Add `load_vault_metadata(vault_path)` function to read `vault.yaml` (returns dict with `name` and `tools` or empty defaults)
- [ ] 2.3 Add `save_vault_metadata(vault_path, metadata)` function to write `vault.yaml`
- [ ] 2.4 Implement three-tier tool resolution function: merge `BUILTIN_TOOLS` + global config tools + vault tools (full replacement, not deep merge)
- [ ] 2.5 Update vault name resolution to prefer `vault.yaml` `name` field over `config.yaml` `vault_names`

## 3. Alias System Migration

- [ ] 3.1 Update `resolve_tool_name()` to scan `aliases` fields from all loaded tool definitions instead of reading from `TOOL_ALIASES`
- [ ] 3.2 Update all call sites that reference `TOOL_ALIASES` directly
- [ ] 3.3 Verify alias resolution works for built-in, global config, and vault-defined aliases

## 4. Partial Artifact Support Integration

- [ ] 4.1 Update `importer.py` to check `supported_types` before importing each artifact type; silently skip unsupported types
- [ ] 4.2 Update `scanner.py` probe logic to derive search paths from tool definitions (not hardcoded config dirs) and respect `supported_types`
- [ ] 4.3 Update `creator.py` to validate tool supports the artifact type when using `--here`/`--tools`; error with message if unsupported
- [ ] 4.4 Update `get_tool_config_dirs()` to derive config directories from all loaded tool definitions

## 5. CLI Commands — tool add, rm, show

- [ ] 5.1 Add `art tool add` subcommand to argparse in `cli.py` with all flags: `--skills`, `--commands`, `--agents`, `--global-skills`, `--global-commands`, `--global-agents`, `--alias` (repeatable), `--vault`, `-g`/`--global`
- [ ] 5.2 Implement `handle_tool_add()` handler — validate at least one artifact path provided, build tool definition dict, write to global config or vault.yaml
- [ ] 5.3 Add `art tool rm` subcommand with `name`, `--vault`, `-g`/`--global` flags
- [ ] 5.4 Implement `handle_tool_rm()` handler — remove from global config or vault.yaml, error on built-in-only tools
- [ ] 5.5 Add `art tool show` subcommand with `name` positional arg
- [ ] 5.6 Implement `handle_tool_show()` handler — resolve tool, display name, source (`built-in` / `user global config` / `vault (<name>)`), aliases, artifact support with paths

## 6. Enhanced tool list

- [ ] 6.1 Update `handle_tool_list()` to display table with columns: Name, Source, Skills, Commands, Agents, Aliases
- [ ] 6.2 Show `yes`/`-` for artifact support columns; show source as `built-in`, `user global config`, or `vault:<name>`

## 7. Vault Metadata Integration

- [ ] 7.1 Update `art vault init` handler to write vault name to `vault.yaml` when `--name` is provided
- [ ] 7.2 Update vault name display logic throughout CLI to check `vault.yaml` name first, fall back to `config.yaml` `vault_names`
- [ ] 7.3 Update `art import` handler to load vault tool definitions from `vault.yaml` before tool resolution

## 8. Tests

- [ ] 8.1 Test `GenericToolAdapter`: construction, `supported_types`, `get_destination` for supported/unsupported types, path expansion
- [ ] 8.2 Test three-tier resolution: built-in only, global override, vault override, precedence
- [ ] 8.3 Test `art tool add`/`rm`/`show` CLI commands end-to-end
- [ ] 8.4 Test partial artifact support: import skipping, creation validation, discovery filtering
- [ ] 8.5 Test `vault.yaml` read/write and vault name precedence
- [ ] 8.6 Test alias resolution from tool definitions (built-in, global, vault sources)

## 9. README and Documentation

- [ ] 9.1 Add example in README.md showing `art tool add` for Cursor IDE as a custom tool
- [ ] 9.2 Update README.md tool support section to mention Codex and custom tool support
- [ ] 9.3 Update ROADMAP.md to reflect completed items
