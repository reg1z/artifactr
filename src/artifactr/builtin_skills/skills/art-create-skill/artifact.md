---
description: How to create a new Artifactr skill using `art create skill/<name>`.
version: 0.1
---

# Creating Skills with Artifactr

A **skill** is a directory-based artifact containing an `artifact.md` file. Skills are stored in `skills/<name>/` inside a vault.

## Basic Usage

```sh
art create skill/<name>
art create skill <name>        # equivalent
```

Both forms are equivalent — the slash syntax is a convenient shorthand.

## Examples

```sh
art create skill/my-workflow          # create in default vault
art create skill/my-workflow -v work  # create in vault named "work"
art create skill/my-workflow --edit   # open in editor after creating
```

## Flags

| Flag | Description |
|---|---|
| `-v`, `--vault` | Target vault (name or path). Defaults to the configured default vault. |
| `-e`, `--edit` | Open the new artifact in `$EDITOR` immediately after creation. |
| `-t`, `--tool` | Tool context (e.g., `claude-code`, `opencode`). |

## What Gets Created

```
<vault>/skills/<name>/
  artifact.md    # the skill content file; edit this with your instructions
```

The `artifact.md` file is pre-populated with a minimal YAML frontmatter block:

```markdown
---
description: ""
---

# <name>

Your skill instructions here.
```

## Slash Syntax

The slash syntax (`art create skill/<name>`) is consistent across `create`, `edit`, `cat`, `inspect`, `export`, and `ls` subcommands.

## See Also

- `art edit skill/<name>` — open an existing skill in `$EDITOR`
- `art spelunk` — discover skills in the current project
- `art proj import` — import skills from vault into the current project
