## Context

Artifactr currently supports importing artifacts as either copies (`art proj import`) or symlinks (`art proj import --link`). Once imported, there is no way to toggle between these states. The `.art-cache/imported` file tracks which artifacts were imported but not whether they are linked or copied. Windows users cannot create symlinks without Developer Mode or admin privileges. There is no protection against overwriting local edits when re-linking.

Key modules:
- `importer.py`: `copy_with_prompt()` handles symlink/copy logic, `update_import_cache()` manages `.art-cache`
- `cli.py`: Command registration and handler functions for `proj`/`conf` namespaces
- `scanner.py`: `load_import_cache()` parses `.art-cache/imported` for display

## Goals / Non-Goals

**Goals:**
- Allow users to toggle artifacts between linked and copied states after import
- Track link state and vault paths in `.art-cache/imported`
- Protect local edits with backup + diff detection when linking over modified files
- Provide a no-privilege-required linking option on Windows via hard links
- Support glob patterns for targeting artifacts by name pattern
- Gracefully skip no-op `art store` operations on already-linked artifacts

**Non-Goals:**
- Conflict resolution or merge tooling for diverged linked artifacts
- Automatic sync scheduling or file watchers
- Junction support for directories on Windows (hard links cover the per-file architecture)
- Migration tooling for existing `.art-cache` files (backward-compatible format change)

## Decisions

### 1. Dedicated `link`/`unlink` subcommands (not flags on `import`)

**Decision**: Add `link` and `unlink` as subcommands in both `proj` and `conf` namespaces with aliases `ln`/`uln`.

**Alternatives considered**:
- Flags on `import` (`--unlink`): Semantically confusing — "importing" when you're converting in place
- A single `sync` command with `--link`/`--unlink` flags: Implies more complexity than warranted and the bare `sync` behavior is ambiguous

**Rationale**: Clean semantics, discoverable, composable with existing `--link` on import.

### 2. `--all`/`-a` required for bulk operations

**Decision**: `art proj link` and `art proj unlink` without arguments or `--all` MUST error. Users must either specify artifact names/patterns or pass `--all`/`-a`.

**Rationale**: Prevents accidental mass linking/unlinking. The deliberate `--all` flag mirrors `rm` safety conventions.

### 2a. Vault-scoped operations (default vault)

**Decision**: All link/unlink operations (both named patterns and `--all`) are scoped to the currently selected default vault. Only artifacts imported from that vault are targeted. Use `--vault`/`-V` to override — the flag is repeatable and supports comma-separated values to target multiple vaults.

**Alternatives considered**:
- Operating on all vaults by default: Too broad — users importing from multiple vaults would accidentally link/unlink artifacts they didn't intend to touch.
- Requiring `--vault` always: Too verbose for the common case where the user has a single default vault.

**Rationale**: The default vault is the natural scope for most operations. Multi-vault users can explicitly expand scope with `-V`. This mirrors how `import` already defaults to the default vault. Named patterns and glob matching are also vault-scoped — if you run `art proj link helping-hand`, it only matches `helping-hand` from the default vault, not from other vaults that may have imported an artifact with the same name.

### 3. Backup to `.art-cache/backups/<date>/<type>/<artifact>`

**Decision**: When `link` replaces a local copy that differs from the vault version, back up to `.art-cache/backups/YYYY-MM-DD/<artifact_type>/<artifact_name>/`. The date format is `YYYY-MM-DD` (e.g., `2025-12-31`). Multiple backups on the same day overwrite earlier ones.

**Rationale**: Project-local, already gitignored via `.art-cache`, organized by date for easy cleanup.

### 4. Interactive diff prompt

**Decision**: When `link` detects a local copy differs from the vault version, prompt with `[b]ackup and link / [s]kip / [l]ink anyway`. The `--force`/`-f` flag auto-selects "backup and link" (safe default).

**Rationale**: Three options cover all user intents. Force mode backs up rather than discarding — safety by default even in scripted usage.

### 5. Windows hard link fallback

**Decision**: On Windows, attempt `Path.symlink_to()` first. If it raises `OSError` (privilege failure), prompt the user to approve falling back to `os.link()` (hard links). Hard links require same-volume — if that also fails, error with a message suggesting Developer Mode.

**Alternatives considered**:
- Junctions (`_winapi.CreateJunction()`): Only work for directories, but the current architecture links individual files, not directories. Unnecessary complexity.
- Silently falling back without prompting: Users should understand they're getting hard links, which behave differently from symlinks.

**Rationale**: Hard links cover the per-file architecture. The prompt ensures informed consent. The error message provides a clear path forward.

### 6. Extended `.art-cache/imported` format

**Decision**: Add a `[vault_paths]` section header for vault label-to-path mapping, and append `:linked`, `:copied`, or `:win_hardlinked` suffixes to each imported entry. Entries without a suffix (legacy) are treated as `:copied`.

```
[vault_paths]
favorites=/home/user/.config/artifactr/vaults/main

[imported]
favorites.claude-code.helping-hand:linked
favorites.claude-code.code-review:copied
favorites.claude-code.have-fun:win_hardlinked
```

**Alternatives considered**:
- JSON/TOML: More structured but a larger migration. The line-based format is simple and sufficient for current needs.
- Separate companion file for vault paths: Adds file management complexity without clear benefit vs a section header.

**Rationale**: Minimal format change, backward compatible, easy to parse with a two-pass approach (headers first, then entries).

### 7. Glob pattern matching via `fnmatch`

**Decision**: Artifact name arguments in `link`/`unlink` commands support glob patterns (matched via Python's `fnmatch.fnmatch`). Patterns are matched against artifact names from `.art-cache/imported`.

**Rationale**: `fnmatch` is stdlib, well-understood, and handles `*`, `?`, `[seq]` patterns. Users must quote patterns to prevent shell expansion.

### 8. `art store` graceful skip for linked artifacts

**Decision**: When `art store` encounters a source artifact that is a symlink resolving to the target vault, skip it with a message rather than redundantly copying.

**Rationale**: No-op detection prevents wasted I/O and user confusion. Comparing `src.resolve()` against the vault destination path is a simple check.

### 9. Inode heuristic for hard link detection

**Decision**: Use `os.stat()` to compare `st_dev` and `st_ino` between project files and vault files as a backup heuristic when `.art-cache` metadata is missing or corrupted. This works on both Unix (inode) and Windows (NTFS file index).

**Rationale**: Small utility function, useful as a sanity check during `unlink` and for `art proj ls` link status display.

## Risks / Trade-offs

- **Hard links behave differently from symlinks**: Editing a hard-linked file edits the vault data (same as symlinks), but `is_symlink()` returns False. Detection relies on `.art-cache` metadata or inode comparison. → Mitigation: Track state in cache, use inode heuristic as backup, document differences for users.

- **Same-volume requirement on Windows**: Hard links fail across volumes. → Mitigation: Clear error message directing users to enable Developer Mode for cross-volume linking.

- **Shell glob expansion**: Users typing `art proj link skill-*` without quotes will have the shell expand the glob before the CLI sees it. → Mitigation: Document quoting requirement in help text.

- **Backup accumulation**: `.art-cache/backups/` could grow over time. → Mitigation: Out of scope for this change; could add cleanup command later. Daily granularity limits growth.

- **Cache format migration**: Existing `.art-cache/imported` files lack the `[vault_paths]` section and suffixes. → Mitigation: No migration needed — parser treats lines without section headers as `[imported]` entries and lines without suffixes as `:copied`.
