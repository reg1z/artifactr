---
description: How to create a new Artifactr command using `art create command/<name>`.
version: 0.1
---

# Creating Commands with Artifactr

A **command** is a flat `.md` file artifact stored in `commands/<name>.md` inside a vault. Commands are concise, token-efficient instructions intended to be used as slash commands.

## Basic Usage

```sh
art create command/<name>
art create command <name>      # equivalent
art create cmd/<name>          # alias: cmd
art create c/<name>            # alias: c
```

All forms are equivalent — the slash syntax is a convenient shorthand.

## Examples

```sh
art create command/run-tests          # create in default vault
art create cmd/run-tests -v work      # create in vault named "work"
art create command/run-tests --edit   # open in editor after creating
```

## Flags

| Flag | Description |
|---|---|
| `-v`, `--vault` | Target vault (name or path). Defaults to the configured default vault. |
| `-e`, `--edit` | Open the new artifact in `$EDITOR` immediately after creation. |
| `-t`, `--tool` | Tool context (e.g., `claude-code`, `opencode`). |

## What Gets Created

```
<vault>/commands/<name>.md    # the command content file; edit this with your instructions
```

The file is pre-populated with a minimal YAML frontmatter block:

```markdown
---
description: ""
---

Your command instructions here.
```

## Slash Syntax

The slash syntax (`art create command/<name>`) is consistent across `create`, `edit`, `cat`, `inspect`, `export`, and `ls` subcommands.

## See Also

- `art edit command/<name>` — open an existing command in `$EDITOR`
- `art create skill/<name>` — create a skill (directory-based artifact)
- `art proj import` — import commands from vault into the current project
