## Why

Several small UX inconsistencies have accumulated in the CLI that create friction for everyday use: `art spelunk` without a target silently targets global config instead of the obvious default (CWD), `art create` lacks the slash-prefix syntax that most other artifact commands already support, the `art nav` shell wrapper swallows `--help` output, and the main help text labels artifact commands under "Vault Operations" — a misnomer that confuses them with the `art vault` namespace. These are all low-risk, high-leverage fixes with no breaking changes.

## What Changes

- **`art spelunk` CWD default**: When no positional target is given, spelunk the current working directory instead of global config. The `-g`/`--global` flag becomes the deliberate path to spelunk global config.
- **Version bump**: Package version advances to `0.3.2` (`pyproject.toml` + `__init__.py`).
- **`-V` shorthand for `--version`**: The top-level `art` parser gains `-V` as a short alias for `--version`.
- **`art nav --help` fix**: Shell wrapper snippets (bash, zsh, fish, powershell) detect `--help`/`-h` flags and pass through directly, avoiding the current behavior where help text is captured into `$()` and `cd` fails.
- **`art create` slash syntax**: `art create skill/my-skill` becomes equivalent to `art create skill my-skill`, consistent with `edit`, `cat`, `inspect`, `export`, and `ls`.
- **Help text rename**: "Vault Operations" section in the main `art --help` epilog renamed to "Artifact Operations".

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `discovery`: Spelunk now defaults to CWD when no target is provided; `-g`/`--global` is now the explicit path to global config spelunking.
- `creation`: `art create` gains slash-prefix syntax (`type/name`) as an alternative to the two-positional form.
- `artifact-navigation`: Shell wrapper must handle `--help`/`-h` flags by routing them directly through `command art` instead of into the `--print` capture path.
- `cli`: Top-level `-V`/`--version` shorthand added; main help epilog section renamed from "Vault Operations" to "Artifact Operations".

## Impact

- `src/artifactr/cli.py`: `handle_spelunk()`, `_main()` (argv pre-processing for create slash syntax), top-level parser (`-V`/`--version`, epilog rename)
- `src/artifactr/utils.py`: `get_shell_wrapper_snippet()` for all four shell variants
- `src/artifactr/__init__.py`: version string
- `pyproject.toml`: version string
- Tests: spelunk tests expecting global-config default behavior when no target is given will need updating
