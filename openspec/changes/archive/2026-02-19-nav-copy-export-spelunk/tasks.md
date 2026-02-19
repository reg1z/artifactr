## 1. Frontmatter Name Resolution Convention

- [x] 1.1 Update `AGENTS.md` to document frontmatter `name:` fallback as a project-wide artifact name-matching convention (not scoped to `art edit`)
- [x] 1.2 Confirm `_find_by_frontmatter_name()` and `_parse_frontmatter_name()` in `creator.py` are reusable from outside `art edit` (no edit-specific assumptions)

## 2. Spelunk Output Restructure

- [x] 2.1 Remove TOOL column from `handle_spelunk` human-format rendering in `cli.py`
- [x] 2.2 Add LOCATION column: compute `artifact["path"].relative_to(original_target)` for all non-global spelunk modes
- [x] 2.3 Add home-collapsed path logic for global spelunk LOCATION (`~/` prefix)
- [x] 2.4 Handle `ValueError` from `relative_to()` (symlink outside search root) by falling back to absolute path
- [x] 2.5 Remove DESCRIPTION column from default human-format output
- [x] 2.6 Add `--verbose` / `-v` flag to `spelunk` subparser that re-enables the DESCRIPTION column
- [x] 2.7 Update markdown format output: replace Source/Path columns with Location column
- [x] 2.8 Update spelunk tests to reflect new column structure

## 3. `art nav` — Core Command

- [x] 3.1 Add `nav_mode` field support to `config.py` (read/write from `config.yaml`)
- [x] 3.2 Add `nav` subparser to `cli.py` with positional `target` (optional), `--print`, `--spawn` / `-s`, `--window` / `-w` flags
- [x] 3.3 Implement target resolution logic in `handle_nav`: type alias → vault name → `vault/type` path → error
- [x] 3.4 Implement `--print` mode: output resolved path to stdout
- [x] 3.5 Implement `--spawn` mode: launch interactive subshell at resolved path via `subprocess.run`
- [x] 3.6 Implement `--window` mode: best-effort new terminal window using `$TERMINAL`, platform fallback list
- [x] 3.7 Implement `nav_mode` config fallback (if no flag, read config; if neither, print error with instructions)
- [x] 3.8 Add vault name collision warning to `handle_vault_add` and `handle_vault_init` for reserved type tokens

## 4. `art shell setup` Command

- [x] 4.1 Add shell detection utility to `utils.py`: detect shell from `$SHELL` (Unix) or PowerShell environment
- [x] 4.2 Define shell wrapper snippets for bash/sh, zsh, fish, PowerShell
- [x] 4.3 Add `shell` namespace parser and `setup` subcommand parser to `cli.py`
- [x] 4.4 Implement `handle_shell_setup`: detect shell, identify rc file, prompt to preview snippet, prompt to confirm, append snippet
- [x] 4.5 Handle fish special case: write to `~/.config/fish/functions/art.fish`, warn if file exists, ask to confirm overwrite
- [x] 4.6 Support `-y` / `--yes` flag to skip all prompts in `handle_shell_setup`
- [x] 4.7 Print post-install `source` instruction after successful write

## 5. `art copy` Command

- [x] 5.1 Implement source resolution logic: parse `[vault/][type/]name` from positional argument (support all type aliases)
- [x] 5.2 Implement destination resolution logic: trailing slash → container vault; no trailing slash + registered vault name → container vault; otherwise → artifact name
- [x] 5.3 Implement single-artifact copy: locate source file/dir, copy to destination path, preserve type structure
- [x] 5.4 Implement same-vault duplicate: copy artifact to new name within same vault
- [x] 5.5 Implement cross-vault copy: copy artifact to corresponding type subdir in destination vault
- [x] 5.6 Integrate frontmatter name fallback into source resolution (reuse `_find_by_frontmatter_name`)
- [x] 5.7 Implement multi-type name conflict detection: error with type-prefix hint when bare name matches multiple types
- [x] 5.8 Implement glob pattern matching for sources: expand `*`, `type/*`, `type/*-pattern` against vault contents (including frontmatter name fields)
- [x] 5.9 Validate that multi-artifact glob sources require a container destination; error otherwise
- [x] 5.10 Add `copy` subparser to `cli.py` with aliases `cp`; wire to `handle_copy`
- [x] 5.11 Write tests for source resolution, destination resolution, type coercion, glob expansion, and conflict detection

## 6. `art vault copy` Command

- [x] 6.1 Implement vault copy business logic in `catalog.py`: resolve source vault path, determine destination path (explicit path vs. fallback `<config_dir>/vaults/<name>/`)
- [x] 6.2 Copy `skills/`, `commands/`, `agents/`, `vault.yaml` to destination (default mode)
- [x] 6.3 Implement `--all` / `-a` flag: copy all vault contents except `.git/`
- [x] 6.4 Update `vault.yaml` in the copy with the new vault name (preserve all other fields)
- [x] 6.5 Auto-register the copied vault in `config.yaml`
- [x] 6.6 Error if destination path already exists
- [x] 6.7 Add `copy` / `cp` subparser under the `vault` namespace; wire to `handle_vault_copy`
- [x] 6.8 Write tests for default copy scope, `--all` flag, auto-registration, `vault.yaml` name update

## 7. `art vault export` Command

- [x] 7.1 Implement `export_vaults()` business logic in `catalog.py`: accept list of vault paths, output zip path
- [x] 7.2 Build zip with `zipfile.ZipFile` (ZIP_DEFLATED): per-vault dirs containing `skills/`, `commands/`, `agents/`, `vault.yaml`
- [x] 7.3 Generate and write `manifest.yaml` to archive root: list of `{name, dir}` entries
- [x] 7.4 Implement vault selection: comma-separated names, glob pattern matching against registered vault names, `--all` / `-a` flag
- [x] 7.5 Error if no vault specified (no name, no glob, no `--all`); error if output path already exists
- [x] 7.6 Add `export` subparser under the `vault` namespace with vault positional (optional) and `--all` / `-a`; wire to `handle_vault_export`
- [x] 7.7 Write tests for single-vault export, multi-vault export, glob selection, `--all`, manifest structure

## 8. `art vault import` Command

- [x] 8.1 Implement `import_vaults()` business logic in `catalog.py`: accept zip path and dest dir, extract, register
- [x] 8.2 Validate input is a readable zip containing `manifest.yaml`; error otherwise
- [x] 8.3 Read `manifest.yaml` to get vault name/dir mappings
- [x] 8.4 Extract zip to destination directory (flat layout: `<dest>/<vault-dir>/`)
- [x] 8.5 Register each extracted vault in `config.yaml` using manifest name; error on name/path conflict without aborting other vaults
- [x] 8.6 Default destination to `<config_dir>/vaults/` when no dest arg provided; print location and vault list; prompt to confirm
- [x] 8.7 Support explicit destination positional argument; still show confirmation (suppressible with `-y`)
- [x] 8.8 Support `-y` / `--yes` to skip confirmation prompts
- [x] 8.9 Add `import` subparser under the `vault` namespace; wire to `handle_vault_import`
- [x] 8.10 Write tests for extraction, manifest parsing, auto-registration, conflict handling, confirmation flow
