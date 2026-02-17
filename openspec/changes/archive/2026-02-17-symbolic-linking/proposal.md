## Why

Imported artifacts are either static copies (stale the moment the vault changes) or symlinks (set once at import time with no way to toggle). Users need the ability to switch between linked and copied states after import, protect local edits when re-linking, and have linking work reliably on Windows without requiring elevated privileges. The `.art-cache` also lacks metadata about link state, making it impossible to know which artifacts are symlinked vs copied.

## What Changes

- Add `link` (`ln`) and `unlink` (`uln`) subcommands to both the `project` and `config` namespaces for toggling artifacts between symlinked and copied states after import
- Require `--all`/`-a` for bulk link/unlink operations to prevent accidental mass changes
- Scope all link/unlink operations to the default vault; use `--vault`/`-V` (repeatable, comma-separated) to target other vaults
- Support glob patterns (via `fnmatch`) for targeting artifacts by pattern (e.g., `"skill-*"`)
- Add backup mechanism (`.art-cache/backups/<date>/<artifact_type>/<artifact>`) to protect local edits when linking replaces a modified local copy
- Add diff detection and interactive prompt (`[b]ackup / [s]kip / [l]ink anyway`) when linking over a locally modified artifact
- Extend `.art-cache/imported` format to track link state (`:linked`, `:copied`, `:win_hardlinked`) and vault paths (`[vault_paths]` section)
- Add Windows fallback: attempt symlink first, then offer hard link (`os.link()`) as a no-privilege-required alternative with user approval
- Add graceful skip in `art store` when source artifact is already a symlink pointing to the target vault
- Add inode-based heuristic (`os.stat()` comparison) for detecting hard-linked files as a backup when cache metadata is missing

## Capabilities

### New Capabilities
- `artifact-linking`: Link/unlink subcommands, glob pattern matching, backup mechanism, diff detection, and link state toggling for both project and config namespaces
- `windows-link-fallback`: Windows-specific hard link fallback with privilege detection, same-volume validation, and user-facing guidance
- `import-cache-v2`: Extended `.art-cache/imported` format with `[vault_paths]` section and `:linked`/`:copied`/`:win_hardlinked` suffixes, plus backward compatibility for legacy format

### Modified Capabilities
- `project-commands`: Add `link`/`unlink` subcommands with aliases `ln`/`uln`
- `config-commands`: Add `link`/`unlink` subcommands with aliases `ln`/`uln`
- `store-force`: Add symlink-to-same-vault detection and graceful skip

## Impact

- `src/artifactr/importer.py`: New linking/unlinking functions, backup logic, Windows fallback, cache format updates
- `src/artifactr/cli.py`: New subcommand registrations (link/unlink in proj + conf), argument parsing, handler functions
- `src/artifactr/scanner.py`: Updated cache parsing for new format (backward compatible)
- `.art-cache/imported`: Format change (additive — old entries without suffix treated as `:copied`)
- Cross-platform: Windows users get hard link fallback; Linux/macOS behavior unchanged
