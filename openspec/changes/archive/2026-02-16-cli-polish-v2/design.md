## Context

Artifactr's CLI uses argparse with manual alias definitions (`aliases=[]` on `add_parser()`) and a hand-crafted epilog for `art --help`. A first round of polish (v0.0.8) added `ls`/`list` aliases and single-letter namespace aliases (`v`, `t`, `p`, `c`). This second round extends aliases to the remaining top-level commands and edit subcommands, adds missing UX features, and improves help text.

Current state:
- `vault`→`v`, `tool`→`t`, `project`→`proj`/`p`, `config`→`conf`/`c`, `list`→`ls` all exist
- No aliases for `spelunk`, `store`, `create`, `edit`, or edit subcommands
- `art store` has no `--force` flag — overwrites always prompt for confirmation
- Spelunk shows `(imported: vault_name)` but doesn't verify the source still exists
- Ctrl-C produces a traceback everywhere — no `KeyboardInterrupt` handling
- Top-level namespace help screens (`art vault -h`, etc.) lack descriptive paragraphs

## Goals / Non-Goals

**Goals:**
- Add shorthand aliases for all remaining commands: `spelunk`→`sp`, `store`→`st`, `create`→`cr`, `edit`→`ed`, plus edit subcommand single-letter aliases
- Add `--force`/`-f` to `art store` to overwrite existing artifacts without prompting
- Detect and display orphaned imports in spelunk output
- Handle Ctrl-C cleanly across the entire program
- Add descriptive help text to all top-level command/namespace `-h` screens
- Clarify `config edit` and `config import` help text

**Non-Goals:**
- Refactoring the dispatch logic in `main()` (e.g., switching to a dispatch table)
- Adding aliases to nested subcommands beyond `edit` (e.g., `vault add`→`vault a`)
- Changing the overall help formatting architecture

## Decisions

### 1. Global KeyboardInterrupt handling at entry point

Wrap `main()` in a single `try/except KeyboardInterrupt` in `__main__.py`. This catches Ctrl-C from any point in the program — interactive prompts, long-running operations, subprocess calls — and exits with code 130 (Unix convention: 128 + SIGINT signal 2). Print a newline before exiting to avoid the `^C` leftover on the terminal line.

**Why not per-prompt?** The existing `EOFError` catches already handle Ctrl-D gracefully at each `input()` call with "Aborted." messages. `KeyboardInterrupt` is different — it means "I want out entirely," so a single top-level catch is the right granularity. Keep the per-prompt `EOFError` handlers as-is.

### 2. `art store --force` behavior

When `-f`/`--force` is passed, overwrite existing artifacts in the target vault without prompting for confirmation. The interactive selection menu still appears — `--force` only affects the overwrite behavior when a selected artifact already exists at the destination. This mirrors the existing `--force` semantics elsewhere in the CLI (e.g., `art rm -f` skips confirmation). The flag is passed through to `copy_with_prompt(force=True)`.

### 3. Orphaned import detection in spelunk

Add validation in `handle_spelunk()` after loading the import cache. For each artifact that appears in the import cache:

1. Resolve each vault name to a path using the config's vault catalog
2. If the vault name can't be resolved → append `vault not found` to the display
3. If the vault path exists, check whether the artifact still exists in it → if not, append `source missing`

Display format: `artifact-name (imported: my-vault, source missing)` or `artifact-name (imported: my-vault, vault not found)`.

**Trade-off:** This adds filesystem I/O to the display loop. However, spelunk is already doing substantial I/O (scanning directories), and the import cache is typically small, so the overhead is negligible.

**Implementation:** Add a helper function `check_import_source(artifact_name, artifact_type, vault_name, config)` that returns one of: `None` (source exists), `"source missing"`, or `"vault not found"`. Call it in the spelunk display loop when an artifact is in the import cache.

### 4. Edit alias applied to both top-level and config subcommand

The `ed` alias needs to work for both `art edit` (top-level) and `art config edit` / `art conf ed`. Both are separate `add_parser()` calls, so each gets `aliases=["ed"]` independently.

For edit subcommands (`skill`, `command`, `agent`), the aliases are single letters (`s`, `c`, `a`). The `artifact_type` argument currently uses `choices=["skill", "agent", "command"]` — this needs to change to accept the short forms too, then normalize them to full names before dispatch.

**Approach:** Expand `choices` to `["skill", "s", "agent", "a", "command", "c"]` and add normalization in the handler. This is simpler than subparsers for what is essentially a positional enum.

### 5. Help text descriptions

Add `description=` parameter to all top-level `add_parser()` calls. These appear at the top of each command's own `-h` output. Keep them terse but friendly — one to two sentences explaining what the command does and any important nuances.

For `config edit`: explicitly state it opens artifactr's own global YAML config, not any tool-specific config.
For `config import`: explicitly state it imports artifacts into tool-specific global config directories (e.g., `~/.claude/commands/`), not into artifactr's own config.
For `config` namespace description: mention both tool-specific global configs and artifactr's own configuration.

## Risks / Trade-offs

- **Alias collisions**: `st` for store, `sp` for spelunk, `cr` for create, `ed` for edit — none conflict with existing aliases (`v`, `t`, `p`, `c`). The edit subcommand aliases `s`, `c`, `a` only exist within the edit command's scope, so `c` doesn't conflict with top-level `c` (config). However, `edit c` (command) and `edit` with the `c` alias for the type — these are positional args, not subcommands, so they work differently. The normalization approach handles this cleanly.
- **Orphan detection false positives**: If a vault is temporarily unmounted or on a network drive, artifacts will show as orphaned. This is acceptable — it's informational, not destructive.
