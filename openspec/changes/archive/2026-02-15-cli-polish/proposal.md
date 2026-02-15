## Why

Several CLI usability gaps need addressing: a bug prevents adding multiple tool aliases at once, common namespace commands lack short aliases, the `list` verb is inconsistent with Unix conventions, and there's no way to edit the global config file from the CLI.

## What Changes

- **Fix `art tool add --alias`**: Support comma-separated values (e.g., `--alias a,b`) in addition to the existing repeatable flag (`--alias a --alias b`), and allow mixing both styles.
- **Add `art config edit`**: New subcommand that opens `~/.config/artifactr/config.yaml` in the user's editor, using the same editor resolution precedence as `art edit` (`$VISUAL` → `$EDITOR` → nano/nvim/vim/vi).
- **Add single-letter namespace aliases**: `art p` (project), `art c` (config), `art v` (vault), `art t` (tool) — in addition to existing `proj` and `conf` aliases.
- **Rename `list` → `ls`** across all commands: **BREAKING** — `art list`, `art vault list`, `art tool list`, `art config list`, `art project list` all become `ls`. No backward-compat alias.

## Capabilities

### New Capabilities
- `config-editing`: Opening the global artifactr config file in the user's preferred editor via `art config edit`.

### Modified Capabilities
- `cli`: Adding single-letter aliases for namespace subcommands, renaming `list` → `ls` across all top-level and namespace commands.
- `custom-tools`: Fixing `--alias` flag on `art tool add` to accept comma-separated values.
- `config-commands`: Adding the `edit` subcommand to the config namespace.

## Impact

- `src/artifactr/cli.py`: Parser definitions (aliases, subcommand names) and new `config edit` handler.
- `src/artifactr/utils.py`: Possibly reuse `get_editor()` for config edit.
- Tests: Update any tests referencing `list` subcommands to use `ls`.
- Users: `art <namespace> list` no longer works — must use `ls`.
