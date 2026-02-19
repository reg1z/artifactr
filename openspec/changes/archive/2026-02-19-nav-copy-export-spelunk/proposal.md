## Why

Artifactr's vault and artifact management is maturing, but key navigation, copy, and portability workflows still require manual filesystem operations or multi-step workarounds. These additions round out the core user experience with commands that match familiar UNIX conventions (`cp`, `cd`) and make vaults shareable and portable.

## What Changes

- **`art nav`**: New top-level command that navigates the shell to a vault or artifact-type directory. Supports shell wrapper integration (via `art shell setup`), subshell spawning (`--spawn`), and new terminal window (`--window`). Behavior configurable via `nav_mode` in `config.yaml`.
- **`art shell setup`**: New subcommand of `art` that installs the shell wrapper function into the user's shell rc file, with snippet preview and confirmation prompts.
- **`art copy`**: New top-level command (alias: `art cp`) for copying artifacts within or across vaults. Uses cp-style positional syntax with vault-prefix (`vault/artifact`), type-prefix (`type/artifact`), and trailing-slash container syntax. Supports glob patterns and frontmatter `name` field matching.
- **`art vault copy`**: New subcommand (alias: `art vault cp`) for duplicating an entire vault to a new path. Auto-registers the copy. Copies only artifact directories + `vault.yaml` by default; `--all` includes other files (excluding `.git/`).
- **`art vault export`**: New subcommand for exporting one or more vaults to a `.zip` archive containing artifact directories and a `manifest.yaml`. Supports vault name glob patterns and `--all` flag.
- **`art vault import`**: New subcommand for importing a vault bundle `.zip`, extracting to a destination directory and registering all vaults. Defaults to a fallback location with confirmation.
- **Spelunk column restructure**: Remove TOOL column; add LOCATION column showing path relative to the original search root. Remove DESCRIPTION from default human output; add `--verbose` / `-v` flag to restore it. Fix symlink edge case for `relative_to()` failures.
- **Frontmatter name resolution convention**: Expand the existing edit-by-frontmatter-name fallback (currently scoped to `art edit`) to apply to ALL commands that resolve artifact names by identifier, including `art copy`.

## Capabilities

### New Capabilities

- `artifact-navigation`: `art nav` command with shell integration modes (wrapper, spawn, window, print), `art shell setup` for rc file installation across bash/zsh/sh/fish/PowerShell, and `nav_mode` config field.
- `artifact-copy`: `art copy` (alias `art cp`) with cp-style positional syntax, vault-prefix, type-prefix, trailing-slash container targets, glob matching, and frontmatter name fallback.
- `vault-copy`: `art vault copy` (alias `art vault cp`) for cloning a vault to a new path, with selective file inclusion and auto-registration.
- `vault-export-import`: `art vault export` and `art vault import` for zip-based vault portability with manifest, glob/`--all` selection, and confirmation-guarded extraction.

### Modified Capabilities

- `spelunk-output-formats`: Human-format column structure changes (TOOL removed, LOCATION added, DESCRIPTION moved behind `--verbose`); location is always relative to original search root.
- `artifact-editing`: Frontmatter `name` field fallback for artifact name resolution is now a project-wide convention, not scoped to `art edit` alone. All artifact name-matching commands MUST apply filename/dirname match first, then frontmatter fallback.

## Impact

- `src/artifactr/cli.py`: New handlers for `nav`, `shell setup`, `copy`, `vault copy`, `vault export`, `vault import`; updated spelunk handler for column restructure
- `src/artifactr/catalog.py`: Vault copy and export/import business logic
- `src/artifactr/config.py`: `nav_mode` config field read/write
- `src/artifactr/scanner.py`: Spelunk location relativization (path relative to search root)
- `src/artifactr/utils.py`: Shell detection for `art shell setup`
- `AGENTS.md`: Document frontmatter name resolution as a project-wide convention
- No new external dependencies (zip via stdlib `zipfile`, YAML via existing PyYAML)
