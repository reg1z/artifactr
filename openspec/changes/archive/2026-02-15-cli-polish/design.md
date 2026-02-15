## Context

Artifactr is at v0.0.7 with no established userbase, so breaking changes are acceptable. The CLI is built with Python's `argparse`. Editor resolution logic already exists in `utils.get_editor()`. The `--alias` flag on `art tool add` uses `action="append"` which stores comma-separated input as a single string rather than splitting it.

## Goals / Non-Goals

**Goals:**
- Fix the alias comma-separation bug so `--alias a,b` works
- Add `art config edit` for editing the global config file
- Add single-letter aliases (`p`, `c`, `v`, `t`) for namespace commands
- Rename all `list` subcommands to `ls`

**Non-Goals:**
- Adding backward-compat aliases for `list` → `ls`
- Changing the `art edit` command (that's for artifacts, not config)
- Adding `-t` shorthand for `--tools`

## Decisions

### Alias comma-split: post-process in handler
**Decision**: After argparse parses `--alias` values (still using `action="append"`), post-process the list by splitting each element on commas and flattening. This preserves support for `--alias a --alias b`, adds `--alias a,b`, and allows mixing both.

**Rationale**: Simpler than a custom argparse type. Consistent with how `--tools` is already handled throughout the codebase (comma-separated string, split later). One line of code: `aliases = [a for raw in args.aliases for a in raw.split(",")]`.

### Config edit: reuse get_editor()
**Decision**: The `art config edit` handler calls `get_editor()` from `utils.py` and opens the config file path from `get_config_dir() / "config.yaml"`. Same pattern as `_handle_edit`.

**Rationale**: No new logic needed. `get_editor()` already implements the correct precedence ($VISUAL → $EDITOR → fallback chain). `get_config_dir()` already exists in `utils.py`.

### Single-letter aliases: argparse aliases parameter
**Decision**: Add to the `aliases=` list on each `add_parser()` call:
- `"project", aliases=["proj", "p"]`
- `"config", aliases=["conf", "c"]`
- `"vault", aliases=["v"]`
- `"tool", aliases=["t"]`

**Rationale**: Native argparse feature. Zero overhead.

### list → ls: direct rename
**Decision**: Change the subcommand name from `"list"` to `"ls"` in all `add_parser()` calls. No aliases for the old name.

**Rationale**: Pre-1.0 with no userbase. Clean break. `ls` matches Unix conventions.

## Risks / Trade-offs

- **[Breaking: `list` → `ls`]** → Acceptable at v0.0.7 with no real userbase. No mitigation needed.
- **[`art config edit` differs from other config subcommands]** → Other `config` subcommands operate on global tool config directories, while `edit` operates on artifactr's own config file. The semantic difference is intentional and the command name is self-documenting.
- **[Single-letter `c` could conflict with future commands]** → `c` at the subparser level is unambiguous since `create` is already a separate top-level command, not a namespace. Acceptable.
