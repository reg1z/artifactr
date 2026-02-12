## Why

Artifactr can discover, store, and import artifacts, but has no way to create one from scratch. Users must manually create directory structures and write YAML frontmatter by hand. A guided creation command — especially for skills, which have the richest structure — would close this gap in the artifact lifecycle and make the tool more accessible.

## What Changes

- Add `art create skill <name>` command that scaffolds a new skill with a `SKILL.md` containing YAML frontmatter
- Default creation target is the default vault; `--here` flag creates in the current project's tool config directory instead
- Flag-based creation: `-d/--description` (required), `-n/--name`, `-c/--content`, `-D/--field key=value`
- Add `textual` as a new dependency alongside PyYAML (for future TUI work on a separate branch)

**Deferred to separate branch (TUI):**
- Interactive mode via a Textual TUI form — decoupled from CLI for now, lives on the `TUI` branch

## Capabilities

### New Capabilities
- `creation`: The `art create skill` command — scaffolding logic, vault vs project targeting, flag-based mode, frontmatter generation

### Deferred Capabilities
- `creation-tui`: The Textual TUI form for interactive skill creation — implemented on the `TUI` branch, not wired into CLI on main

### Modified Capabilities
- `cli`: Adding the `create` subcommand with its argument and flag definitions
- `core`: Adding `textual` as a project dependency

## Impact

- **New files**: Creator module (business logic), known-fields registry, TUI module (on `TUI` branch only)
- **Modified files**: `cli.py` (new `create` subcommand), `pyproject.toml` (add textual dependency)
- **Dependencies**: Adds `textual` (and its transitive deps including `rich`) as a new external dependency
- **Tool adapters**: Used by `--here` mode to resolve project-local config directories; no adapter changes needed
