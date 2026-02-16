## Why

The CLI needs a second round of polish to improve discoverability and usability. Several commands lack shorthand aliases (spelunk, store, create, edit), the help text for top-level namespaces doesn't explain what each command does, and there are UX gaps: Ctrl-C in interactive prompts produces tracebacks, `art store` has no `--force` flag to skip overwrite prompts, and `art spelunk` doesn't detect orphaned imports (artifacts imported from vaults that no longer contain them).

## What Changes

- **New aliases**: `spelunk`→`sp`, `store`→`st`, `create`→`cr`, `edit`→`ed` (top-level and `config edit`), plus `edit skill`→`edit s`, `edit command`→`edit c`, `edit agent`→`edit a`
- **`art store --force/-f`**: Overwrite existing artifacts in the target vault without prompting for confirmation
- **Orphaned import detection in spelunk**: When displaying imported artifacts, check whether the source vault/artifact still exists. Show `(imported: vault, source missing)` or `(imported: vault, vault not found)` accordingly
- **Global KeyboardInterrupt handling**: Catch `KeyboardInterrupt` at the program entry point for clean Ctrl-C exits everywhere
- **Help text overhaul**: Add descriptive paragraphs to all top-level command/namespace help screens (`-h`), update `art --help` epilog to show new aliases, clarify `config edit` and `config import` help text

## Capabilities

### New Capabilities

- `command-aliases-v2`: Shorthand aliases for spelunk, store, create, edit, and edit subcommands
- `store-force`: `--force/-f` flag on `art store` to overwrite existing artifacts without prompting
- `orphaned-import-detection`: Detection and display of orphaned imports in spelunk output
- `keyboard-interrupt-handling`: Global clean handling of Ctrl-C across the entire CLI

### Modified Capabilities

- `help-formatting`: Updated epilog with new aliases, descriptive paragraphs for all command help screens, clarified config edit/import help text

## Impact

- `src/artifactr/cli.py`: Alias additions in `create_parser()`, new `--force` arg on store, dispatch updates in `main()`, help text across all commands
- `src/artifactr/__main__.py`: KeyboardInterrupt wrapper
- `src/artifactr/scanner.py` or `cli.py`: Orphan detection logic for spelunk display
- Tests: New tests for aliases, `--force` flag, orphan detection, Ctrl-C handling
