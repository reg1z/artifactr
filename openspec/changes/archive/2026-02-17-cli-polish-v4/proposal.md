## Why

The `-V`/`--vault` flag currently only supports multi-vault (repeatable + comma-separated) on `link`/`unlink` commands. All other commands accept a single vault. Users need to run the same command multiple times to target different vaults. Additionally, import with `--link` gives no indication that artifacts were linked rather than copied, and `proj ls`/`conf ls` don't show link state at all.

## What Changes

- **Multi-vault `-V` expansion**: Make `-V` accept comma-separated and repeatable values across most commands (`import`, `ls`, `store`, `create`, `tool add`, `tool ls`, `tool info`). Keep `rm` and `edit` single-vault for safety.
- **`proj ls`/`conf ls` vault flag**: Add `-V` support to project and config list commands, scoped to previously-imported artifacts from specified vaults.
- **`proj rm`/`proj wipe`/`conf rm`/`conf wipe` vault flag**: Add `-V` support, scoped to previously-imported artifacts from specified vaults.
- **`tool ls --all` flag**: New `-a`/`--all` flag to list custom tool definitions from all catalog vaults.
- **`tool info --all` flag**: New `-a`/`--all` flag to show all tool definitions (built-in, global config, and vault-defined).
- **Import `--link` output**: Show per-line link state in import summary (e.g., `skills: 3 (linked)`).
- **`proj ls`/`conf ls` link state display**: Add arrow indicators (`→` symlinked, `⇒` hardlinked) and a STATE column showing `linked`/`copied`/`hardlinked`.
- **README update**: Document all new functionality under the Extended Usage section, including link/unlink commands, `--link` import, multi-vault `-V`, and link state display.

## Capabilities

### New Capabilities

- `multi-vault-flag`: Unified multi-vault `-V` flag behavior across commands — repeatable, comma-separated, with per-command semantics (import-from, list-across, store-into, create-in).
- `link-state-display`: Display link state in import summaries and list output — arrow indicators, STATE column, per-line link counts.
- `tool-discovery`: `--all` flags for `tool ls` and `tool info` to discover tools across all vaults and built-in definitions.

### Modified Capabilities

- `project-commands`: Add `-V` flag to `proj ls`, `proj rm`, `proj wipe`.
- `config-commands`: Add `-V` flag to `conf ls`, `conf rm`, `conf wipe`.
- `vault-artifact-listing`: Multi-vault support for `art ls`.
- `custom-tools`: Multi-vault support for `tool add`, `tool ls`, `tool info`; `--all` flags.
- `creation`: Multi-vault support for `art create`.
- `importing`: Multi-vault `-V` for import commands.
- `store-force`: Multi-vault support for `art store`.

## Impact

- `src/artifactr/cli.py`: Argument parsing changes for all affected commands, new `--all` flags on tool subcommands.
- `src/artifactr/importer.py`: Import summary output, list output formatting, vault resolution helpers.
- `src/artifactr/scanner.py`: Possible changes for multi-vault listing/store operations.
- `README.md`: Extended Usage section update.
