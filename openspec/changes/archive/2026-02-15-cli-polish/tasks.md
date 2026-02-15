## 1. Rename list → ls

- [x] 1.1 Rename top-level `list` subcommand to `ls` in `cli.py` parser definition
- [x] 1.2 Rename `art vault list` to `art vault ls` in parser definition
- [x] 1.3 Rename `art tool list` to `art tool ls` in parser definition
- [x] 1.4 Rename `art config list` to `art config ls` (and `art conf list` → `art conf ls`)
- [x] 1.5 Rename `art project list` to `art project ls` (and `art proj list` → `art proj ls`)
- [x] 1.6 Update all internal references to `list` subcommand names (dest values, dispatch logic, handler names if applicable)
- [x] 1.7 Update tests referencing `list` subcommands to use `ls`

## 2. Add single-letter namespace aliases

- [x] 2.1 Add alias `p` to `project` subcommand (`aliases=["proj", "p"]`)
- [x] 2.2 Add alias `c` to `config` subcommand (`aliases=["conf", "c"]`)
- [x] 2.3 Add alias `v` to `vault` subcommand (`aliases=["v"]`)
- [x] 2.4 Add alias `t` to `tool` subcommand (`aliases=["t"]`)

## 3. Fix --alias comma separation

- [x] 3.1 In the `art tool add` handler, post-process `args.aliases` to flatten comma-separated values: `aliases = [a.strip() for raw in args.aliases for a in raw.split(",")]`
- [x] 3.2 Add tests for comma-separated aliases, repeatable aliases, and mixed usage

## 4. Add art config edit

- [x] 4.1 Register `edit` subcommand under the `config` namespace parser
- [x] 4.2 Implement `_handle_config_edit` handler: resolve config path via `get_config_dir() / "config.yaml"`, ensure config directory exists, open in editor via `get_editor()`
- [x] 4.3 Add error handling for missing editor (same pattern as `_handle_edit`)
- [x] 4.4 Wire handler into the config subcommand dispatch logic
- [x] 4.5 Add tests for config edit command
