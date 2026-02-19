## Context

Artifactr has solid import/export mechanics for getting artifacts into projects, but lacks:
- A way to navigate the shell to vault/artifact directories (`art nav`)
- A cp-style mechanism for copying artifacts within or across vaults (`art copy`)
- A way to duplicate or back up entire vaults (`art vault copy`, `art vault export/import`)
- Clean spelunk output (TOOL column is misleading; DESCRIPTION is too verbose by default)

These additions touch multiple modules (`cli.py`, `catalog.py`, `config.py`, `scanner.py`, `utils.py`) but introduce no external dependencies. The change uses established patterns from the existing codebase (handler functions, structured result dicts, argparse aliases, `make_help`).

## Goals / Non-Goals

**Goals:**
- Add `art nav` with three navigation modes (shell wrapper, subshell, new window)
- Add `art shell setup` for one-shot shell integration installation
- Add `art copy` with cp-style positional syntax, vault/type prefixes, glob matching
- Add `art vault copy` for cloning a vault
- Add `art vault export` / `art vault import` for zip-based vault portability
- Restructure spelunk human output: remove TOOL, add LOCATION, move DESCRIPTION to `--verbose`
- Generalize frontmatter name resolution to all artifact name-matching commands

**Non-Goals:**
- Network-based vault syncing or remote artifact registries
- GUI or TUI for navigation
- Merge/diff operations between vaults
- Migration tools for `config.yaml` format
- Non-zip export formats (directory export deferred)

## Decisions

### `art nav` — Shell wrapper via hidden `--print` flag

**Decision**: `art nav [target] --print` outputs the resolved path to stdout. A shell function wrapper (installed by `art shell setup`) intercepts `art nav` invocations and evals the result as a `cd` command. The `art nav` binary itself never changes the parent shell's cwd directly.

**Alternatives considered**:
- `--outcmd <tmpfile>` (broot-style): writes `cd /path` to a temp file for the shell function to read. More flexible but heavier; `--print` is sufficient since we only emit a path.
- Subshell-only: Zero setup but nested shell UX is ergonomically worse for frequent use.

**Why this approach**: Industry-standard pattern (nvm, pyenv, zoxide, direnv). One-time setup amortized across all future invocations. `art shell setup` makes setup frictionless.

### `art nav` — `nav_mode` in `config.yaml`

**Decision**: A `nav_mode` field in `config.yaml` controls default behavior (`wrapper | spawn | window | print`). Per-invocation flags (`--spawn`, `-w`/`--window`) override config. If neither is set, error with instructions.

**Alternatives considered**:
- Always require a flag: forces verbosity on every invocation; bad for frequent use.
- Default to `spawn`: silently nests shells, surprising behavior.

**Why this approach**: Config captures stable user preference; flags handle one-off overrides. This pattern is consistent with how tools like `git` and `art` itself handle per-user defaults.

### `art copy` — Positional syntax with vault-prefix, type-prefix, trailing-slash

**Decision**: Source is `[vault/][type/]name-or-glob`. Destination is either `[vault/][type/]name` (rename) or `<vault>/` (trailing slash = copy into vault). All type short aliases (`s/`, `sk/`, `cmd/`, `agt/`, etc.) are valid as type prefixes.

**Alternatives considered**:
- `--from vault-1 --to vault-2` flags: clearer intent but departs from `cp` mental model and is more verbose.
- `art vault copy artifact` (subcommand): separates artifact copy from vault copy but fragments discoverability.

**Why this approach**: Mirrors `cp` conventions that users already know. Trailing-slash convention for containers is universally understood in UNIX tooling.

### Trailing-slash disambiguation

**Decision**: Trailing slash unambiguously signals "copy into this container." Without trailing slash, the last positional is always treated as a new artifact name. If the last positional matches a registered vault name (no trailing slash), treat it as `<vault>/` equivalent.

**Why**: Eliminates all ambiguity without requiring users to remember registration state — trailing slash is always explicit.

### `art vault export` — stdlib `zipfile`, minimal `manifest.yaml`

**Decision**: Use Python's stdlib `zipfile` with `ZIP_DEFLATED` compression. Include a `manifest.yaml` (name-to-dir mapping) but no default-vault metadata (the export is for sharing, not full environment migration).

**Alternatives considered**:
- Raw directory export: simpler but not self-contained for sharing.
- Full `catalog.yaml` with default-vault info: overcomplicated for the primary sharing use case; migration/backup features deferred.

**Why this approach**: No new dependencies. Zip is universally portable. The manifest is the minimum needed to reconstruct vault registration on import.

### Spelunk LOCATION — always relative to original search root

**Decision**: `artifact["path"]` (absolute) is always relativized to `original_target` at display time, not inside scanner functions. Global spelunk uses `~`-collapsed paths. Symlink resolution outside the search tree falls back to absolute path.

**Alternatives considered**:
- Relativize inside `discover_vault_artifacts()`: would produce vault-relative paths (e.g., `skills/my-skill`) even when the vault is found mid-depth-scan — confusing when the user's root is several levels higher.

**Why**: Display logic owns relativization. Scanners produce absolute paths; `handle_spelunk` relativizes everything from one consistent root.

### Frontmatter name resolution — project-wide convention

**Decision**: Filename/dirname match always wins. If no match, scan YAML frontmatter `name:` fields. This fallback applies to all artifact name-matching commands (`art copy`, `art edit`, future commands), not just `art edit`.

**Implementation**: The existing `_find_by_frontmatter_name()` and `_parse_frontmatter_name()` in `creator.py` are already correct — they just need to be called from `art copy`'s resolution logic (and any future command that resolves artifact names).

## Risks / Trade-offs

- **Shell rc file modification**: `art shell setup` appends to rc files. Misdetected shell could write to wrong file. Mitigation: always show the target file path in output; require confirmation by default; use `$SHELL` detection with explicit shell flag override.
- **`--window` platform fragility**: New terminal window requires detecting an installed terminal emulator. Mitigation: try `$TERMINAL` env var first, then a prioritized fallback list; document that `--window` is best-effort.
- **Shell glob expansion on vault names**: `art vault export "claude-*"` requires quoting to prevent shell expansion. Mitigation: document quoting requirement; `--all` flag provides an unambiguous alternative for the common "all vaults" case.
- **`art copy` vault/name ambiguity without trailing slash**: `art copy my-skill vault-2` — is `vault-2` a vault or a new artifact name? Mitigation: if the last positional is a registered vault name (no trailing slash), treat as container; otherwise treat as artifact name. Document this resolution order clearly in `--help`.

## Open Questions

- `art shell setup` — should `--auto` bypass rc file modification directly (for scripting), distinct from `-y` which bypasses prompts but still shows what was done? Deferred; `-y` covers the scripted case adequately.
- `art vault import` — should importing a vault that already exists (same name or overlapping path) merge, skip, or error? Current decision: error with clear message; user must resolve manually.
