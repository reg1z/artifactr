---
description: How to create a new Artifactr agent using `art create agent/<name>`.
version: 0.1
---

# Creating Agents with Artifactr

An **agent** is a flat `.md` file artifact stored in `agents/<name>.md` inside a vault. Agents define sub-agent personas or specialized instruction sets for AI coding tools.

## Basic Usage

```sh
art create agent/<name>
art create agent <name>        # equivalent
art create agt/<name>          # alias: agt
art create a/<name>            # alias: a
```

All forms are equivalent — the slash syntax is a convenient shorthand.

## Examples

```sh
art create agent/code-reviewer          # create in default vault
art create agt/code-reviewer -v work    # create in vault named "work"
art create agent/code-reviewer --edit   # open in editor after creating
```

## Flags

| Flag | Description |
|---|---|
| `-v`, `--vault` | Target vault (name or path). Defaults to the configured default vault. |
| `-e`, `--edit` | Open the new artifact in `$EDITOR` immediately after creation. |
| `-t`, `--tool` | Tool context (e.g., `claude-code`, `opencode`). |

## What Gets Created

```
<vault>/agents/<name>.md    # the agent content file; edit this with your instructions
```

The file is pre-populated with a minimal YAML frontmatter block:

```markdown
---
description: ""
---

Your agent instructions here.
```

## Slash Syntax

The slash syntax (`art create agent/<name>`) is consistent across `create`, `edit`, `cat`, `inspect`, `export`, and `ls` subcommands.

## See Also

- `art edit agent/<name>` — open an existing agent in `$EDITOR`
- `art create skill/<name>` — create a skill (directory-based artifact)
- `art proj import` — import agents from vault into the current project
