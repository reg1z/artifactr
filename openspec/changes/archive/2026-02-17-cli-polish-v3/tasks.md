## 1. Quick Flag & Alias Additions (cli.py parser)

- [x] 1.1 Add `-V` shorthand for `--vault` on all commands: ls, rm, store, edit, create skill, create command, create agent, project import, config import, tool add, tool rm, tool list
- [x] 1.2 Add `create` and `cr` as aliases for `vault init` subcommand
- [x] 1.3 Add extended type aliases for `edit`: expand choices to include `cmd`, `com`, `sk`, `agt`, `ag` alongside existing `s`, `c`, `a`
- [x] 1.4 Add extended type aliases for `create`: register `cmd`/`com` as aliases for `command`, `sk` for `skill`, `agt`/`ag` for `agent` subcommands
- [x] 1.5 Add `--name`/`-n` (dest=`display_name`) to `create agent` parser, matching `create skill`
- [x] 1.6 Add `--yes`/`-y` flag to `vault init` parser
- [x] 1.7 Add `--yes`/`-y` flag to `project import` parser
- [x] 1.8 Add `--depth`/`-d` flag (type=int, default=2) to `spelunk` parser
- [x] 1.9 Add `--format` flag (choices: human, json, yaml, md, markdown; default: human) to `spelunk` parser
- [x] 1.10 Make `store` `target_dir` optional (nargs='?') and add `--global`/`-g` flag
- [x] 1.11 Add `--tools` flag to `store` parser

## 2. Vault Naming Change (catalog.py)

- [x] 2.1 Update `_next_auto_name()` to use `vault-N` pattern instead of `llm-vault-N` (change regex and prefix)

## 3. Vault Init Directory Prompt (catalog.py + cli.py)

- [x] 3.1 Modify `init_vault()` in catalog.py to NOT auto-create directories; instead return a signal when directory doesn't exist
- [x] 3.2 Add confirmation prompt in `handle_vault_init()` in cli.py: prompt user before creating non-existent directory, skip prompt if `--yes`

## 4. Edit Frontmatter Name Resolution (creator.py)

- [x] 4.1 Add `_parse_frontmatter_name(file_path)` helper that reads lines until closing `---` and extracts the `name` field
- [x] 4.2 Add `_find_by_frontmatter_name(artifact_type, name, search_dir)` that scans all artifacts of a type and returns the first match (alphabetical order)
- [x] 4.3 Update `resolve_edit_target()` to call frontmatter fallback when folder/file match fails, for all artifact types (skill, agent, command)
- [x] 4.4 Apply same frontmatter fallback to `--here` mode resolution

## 5. Create Agent Display Name (creator.py + cli.py)

- [x] 5.1 Update `create_artifact()` or agent creation logic to handle `display_name` parameter for agents, writing `name` field to YAML frontmatter
- [x] 5.2 Update `handle_create_artifact()` in cli.py to pass `display_name` for agents (same pattern as skills)

## 6. Project Import Git Flexibility (importer.py + cli.py)

- [x] 6.1 Remove hard `is_git_repo()` error from `import_artifacts()` in importer.py; replace with a return value indicating git status
- [x] 6.2 Add confirmation prompt in `handle_project_import()` in cli.py: prompt when target isn't git, skip prompt if `--yes`, skip `.git/info/exclude` step for non-git targets

## 7. Store Global & Tools (scanner.py + cli.py)

- [x] 7.1 Add validation in `handle_store()`: error if both `target_dir` and `--global` provided; error if neither provided
- [x] 7.2 When `--global` is set, use `discover_global_artifacts()` to find source artifacts instead of scanning `target_dir`
- [x] 7.3 Add `--tools` filtering to store: resolve tool aliases and filter discovered artifacts by tool

## 8. Spelunk Depth Scanning (scanner.py)

- [x] 8.1 Add `discover_artifacts_by_structure(target_path, depth)` function that walks directories up to `depth` levels, looking for `skills/`, `agents/`, `commands/` directories with artifact-shaped content
- [x] 8.2 Integrate depth scanning into `handle_spelunk()`: use as layer-3 fallback when target is neither vault nor tool-config

## 9. Spelunk Output Formats (scanner.py or cli.py)

- [x] 9.1 Define a shared artifact data structure (list of dicts with name, type, path, source fields) used by all spelunk discovery functions
- [x] 9.2 Add `format_spelunk_json(artifacts)` formatter
- [x] 9.3 Add `format_spelunk_yaml(artifacts)` formatter
- [x] 9.4 Add `format_spelunk_markdown(artifacts)` formatter producing a markdown table
- [x] 9.5 Update `handle_spelunk()` to route output through the selected formatter

## 10. Alias Dispatch Updates (cli.py)

- [x] 10.1 Update `_main()` dispatch to recognize `create` and `cr` vault subcommands routing to `handle_vault_init()`
- [x] 10.2 Update artifact type resolution in edit/create handlers to map `cmd`→`command`, `com`→`command`, `sk`→`skill`, `agt`→`agent`, `ag`→`agent`

## 11. Testing

- [x] 11.1 Test vault naming produces `vault-N` pattern
- [x] 11.2 Test vault init prompts on missing directory and respects `--yes`
- [x] 11.3 Test edit frontmatter fallback: folder match priority, frontmatter scan, alphabetical tie-breaking
- [x] 11.4 Test create agent with `--name` produces correct frontmatter
- [x] 11.5 Test project import with non-git target: prompt flow, `--yes` bypass, exclude step skipped
- [x] 11.6 Test store `--global` and `--tools` flags
- [x] 11.7 Test spelunk `--depth` scanning finds nested artifact directories
- [x] 11.8 Test spelunk `--format` outputs valid json, yaml, and markdown
- [x] 11.9 Test all new aliases resolve correctly (`-V`, `create`/`cr` for vault init, `cmd`/`com`/`sk`/`agt`/`ag`)
