## Context

Artifactr is a CLI tool (`art`) for managing AI coding assistant artifacts (skills, commands, agents) across vaults and target repositories. The current command structure has all operations at the top level: `art import`, `art spelunk`, `art store`, etc. This conflates vault-side operations (managing what's in a vault) with project-side operations (managing what's imported into a project) and global config operations (managing what's installed system-wide).

The codebase is Python 3 with argparse, pathlib, and PyYAML. Logic is decoupled from CLI handlers. The tool registry supports built-in tools, global config tools, and vault-scoped tools with three-tier resolution.

Key files: `cli.py` (argparse + handlers), `importer.py` (import logic + git exclude), `scanner.py` (artifact discovery), `config.py` (YAML config I/O), `tools/` (tool adapter system).

## Goals / Non-Goals

**Goals:**
- Restructure CLI into `proj`/`conf` namespaces that clearly separate project-side and global-config operations
- Add vault content management commands (`art list`, `art rm`)
- Add type-filter flags (`-S`/`-C`/`-A`) as a cross-cutting feature reusable across many commands
- Make `spelunk` more versatile: optional target, global config default, vault detection
- Add `--no-exclude` to project import
- Add `proj rm`, `proj wipe`, `proj list` and their `conf` counterparts
- Bump to v0.0.7 with changelog

**Non-Goals:**
- TUI-based interfaces (deferred to future)
- Marketplace integration
- Backward compatibility with `art import` (hard removal, no existing userbase)
- Changes to the tool adapter system or vault metadata format

## Decisions

### Decision 1: Namespace aliases via argparse `aliases` parameter

Argparse's `add_parser()` supports an `aliases` keyword. Both `project`/`proj` and `config`/`conf` will be registered as primary name + alias, avoiding duplicate parser definitions.

```python
subparsers.add_parser("project", aliases=["proj"], help="...")
subparsers.add_parser("config", aliases=["conf"], help="...")
```

**Alternative considered**: Registering two separate subparsers with shared handlers. Rejected because argparse aliases are purpose-built for this and DRY.

### Decision 2: Uppercase short flags for type filters (`-S`/`-C`/`-A`)

Using uppercase avoids collision with common CLI conventions (`-a` for `--all`, `-c` for various things). The `nargs='?'` variant allows optional comma-separated artifact names; the `store_true` variant is used on `rm` commands where artifact names are already positional.

With `nargs='?'`, combined short forms like `-SC` are interpreted as `-S` with value `C` by argparse. Users must use `-S -C` instead. This is acceptable and will be documented.

**Alternative considered**: Lowercase `-s`/`-c`/`-a`. Rejected due to convention collisions across subcommands.

### Decision 3: Shared type-filter argument utilities

A pair of helper functions will be added to avoid repeating the same argparse and resolution logic across ~10 subcommands:

- `add_type_filter_args(parser, allow_names=True)` — adds `-S`/`-C`/`-A` flags with either `nargs='?'` (when `allow_names=True`) or `store_true` (when `allow_names=False`).
- `resolve_type_filters(args)` — reads the parsed args and returns a dict indicating which types to include and optional per-type name lists.

Returns `None` when no filters are specified (meaning "all types"). Returns a dict like `{"skills": True, "commands": ["foo", "bar"], "agents": True}` when filters are active.

These will live in `cli.py` alongside the parser construction.

### Decision 4: cwd-as-default for project and config maintenance commands

All `proj` subcommands use cwd as the default project path. `proj import [target]` makes the positional optional (`nargs='?'`). `proj rm`, `proj wipe`, and `proj list` use `--target` (optional, defaults to cwd). This is safe because:

- `proj rm` and `proj wipe` read `.art-cache` to determine what to delete — if no cache exists, nothing happens.
- `proj wipe` requires interactive confirmation unless `--force` is used.
- `proj list` is read-only.

`conf` subcommands don't need a target — they always operate on the global cache at `~/.config/artifactr/.art-cache-global/`.

### Decision 5: Vault detection in spelunk via `vault.yaml`

When `spelunk` is given a target path, it checks for `vault.yaml` at the root. If present, it treats the target as a vault and scans `skills/`, `commands/`, `agents/` directories directly. Otherwise, it treats the target as a repo and scans tool config directories (`.claude/skills/`, `.opencode/commands/`, etc.).

**Alternative considered**: Checking for the presence of `skills/`/`commands/`/`agents/` directories. Rejected because these directory names could exist in non-vault contexts. `vault.yaml` is an intentional marker.

### Decision 6: `--no-exclude` as a simple boolean on `proj import`

When `--no-exclude` is set, no artifact paths are added to `.git/info/exclude`. The `.art-cache` directory is still excluded regardless (it's internal metadata). Import cache tracking in `.art-cache/imported` is always performed regardless of `--no-exclude`.

### Decision 7: `art rm` (vault-side) without type filter flags

Vault artifact removal requires deliberate action. Users specify artifact names positionally, with optional `type/name` prefix for disambiguation (e.g., `skills/foo`). Interactive confirmation is shown with a summary of what will be removed. `--force` skips the prompt. No `-S`/`-C`/`-A` flags — the existing `resolve_artifact_names` disambiguation flow handles conflicts.

### Decision 8: Cache cleanup for project/config rm and wipe

`proj rm` and `proj wipe` must update `.art-cache/imported` to remove entries for deleted artifacts. `conf rm` and `conf wipe` do the same for `~/.config/artifactr/.art-cache-global/imported`. A shared utility function will handle cache entry removal by artifact name.

`proj wipe` and `conf wipe` read the cache to determine which files to delete, then clear the cache. The type filter flags (`-S`/`-C`/`-A`) on wipe filter which cached entries (and their corresponding files) are removed.

### Decision 9: Global spelunk scans all tool global paths

When spelunking global configs (no target or `-g`), the scanner iterates all configured tools (built-in + global config + default vault) and checks each tool's `global_*` paths. This reuses the existing tool registry but accesses global paths instead of repo-local paths. A new function `get_tool_global_dirs()` (or similar) will be added to the tools module.

## Risks / Trade-offs

- **Breaking change (`art import` removal)**: No existing userbase, so zero migration cost. Hard removal is cleanest.
- **`nargs='?'` flag interaction with combined short forms**: `-SC` won't work as expected. Mitigation: document that `-S -C` must be used separately. Uppercase flags reduce the chance users attempt combining.
- **cwd default on `proj import`**: Could import into the wrong directory if user is in an unexpected location. Mitigation: import requires the target to be a git repo (validation) and shows a summary of what was imported.
- **Cache-based wipe**: If `.art-cache` is manually deleted or corrupted, `proj wipe` won't know what to clean. Mitigation: `proj wipe` should handle missing/empty cache gracefully with a clear message.
