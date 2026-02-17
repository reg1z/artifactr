## Why

The CLI has accumulated several usability gaps: missing shorthand flags, inconsistent alias coverage, rigid git-only import requirements, and limited discovery output. This polish pass addresses these friction points to make the tool feel more complete and ergonomic before expanding the user base.

## What Changes

- `art vault init`: Prompt user before creating non-existent target directories; add `--yes`/`-y` to auto-confirm; add `create`/`cr` as aliases for `init`
- `--vault` flag: Add `-V` shorthand across all commands that accept `--vault`
- `art edit`: Support resolving artifacts by YAML frontmatter `name` field as a fallback when folder/file name doesn't match
- `art edit` & `art create`: Add additional subcommand type aliases (`cmd`/`com`, `sk`, `agt`/`ag`)
- `art create agent`: Add `--name`/`-n` flag for frontmatter display name (parity with `art create skill`)
- `art project import`: Remove hard git requirement; prompt when target isn't a git repo with option to continue; support `--yes`/`-y`
- `art store`: Add `--global`/`-g` flag to store from global tool configs; add `--tools` flag for multi-tool source targeting
- Default vault naming: Change auto-name pattern from `llm-vault-N` to `vault-N`
- `art spelunk`: Add `--depth`/`-d` flag (default 2) for recursive artifact-shaped directory scanning; add `--format` flag supporting `human`, `json`, `yaml`, `md`/`markdown` output formats

## Capabilities

### New Capabilities
- `spelunk-output-formats`: Structured output formats for the spelunk command (human, json, yaml, markdown)
- `spelunk-depth-scanning`: Depth-controlled recursive scanning for artifact-shaped directories beyond vault/tool-config structures
- `confirmation-prompts`: Interactive confirmation prompts with `--yes`/`-y` auto-accept across vault init and project import

### Modified Capabilities
- `vault-init`: Add directory creation prompt, `--yes`/`-y` flag, and `create`/`cr` aliases
- `vaults`: Change default auto-naming from `llm-vault-N` to `vault-N`
- `artifact-editing`: Add frontmatter `name` fallback resolution for all artifact types
- `command-aliases-v2`: Add `cmd`/`com`, `sk`, `agt`/`ag` type aliases for edit and create subcommands
- `creation`: Add `--name`/`-n` to `art create agent`
- `project-commands`: Remove git-only restriction on project import; add `--yes`/`-y` support
- `store-force`: Add `--global`/`-g` and `--tools` flags (expanding store scope beyond the force flag)
- `cli`: Add `-V` shorthand for `--vault` across all commands; register new spelunk flags
- `discovery`: Add depth-based scanning and structured output format support to spelunk

## Impact

- **Files**: `cli.py` (parser definitions, handlers), `catalog.py` (auto-naming, init prompt), `creator.py` (frontmatter resolution), `importer.py` (git requirement removal), `scanner.py` (depth scanning, output formatting)
- **APIs**: No breaking changes; all additions are backwards-compatible
- **Dependencies**: No new dependencies
