---
description: How to create a new Artifactr skill using `art cr s <name>`.
version: 0.2
---

# Creating Skills with Artifactr

A **skill** is a directory-based artifact containing an `artifact.md` file. Skills are stored in `skills/<name>/` inside a vault.

## Basic Usage

```sh
art cr s <name> -d 'description text'
```

The `-d` flag (description) is required. Slash syntax is also supported: `art cr s/<name>`.

### Command & Type Aliases

| Full | Shortest |
|---|---|
| `art create skill` | `art cr s` |

## Examples

```sh
art cr s my-workflow -d 'Workflow automation'
art cr s my-workflow -d 'Workflow helper' -V work        # target vault "work"
art cr s my-workflow -d 'Builds things' -c 'Step 1...'   # with body content
art cr s my-workflow -d 'Helper' -n 'My Workflow'        # custom display name
art cr s my-workflow -d 'Local skill' -H                 # create in CWD project, not vault
art cr s my-workflow -d 'Helper' -D version=1.0 -D author=Jo   # create with additional frontmatter field(s)
art cr s my-workflow -d 'Helper' --tools claude-code,opencode  # create in tool(s) config
```

## Flags

| Flag | Description |
|---|---|
| `-d`, `--description` | **Required.** Skill description (populates frontmatter `description:`). |
| `-c`, `--content` | Markdown body content placed after the frontmatter block. |
| `-n`, `--name` | Override the frontmatter display name (defaults to the identifier). |
| `-D`, `--field` | Additional frontmatter field as `key=value`. Repeatable. |
| `-V`, `--vault` | Target vault (name or path). Comma-separated or repeatable. Defaults to the configured default vault. |
| `-H`, `--here` | Create in the current project directory instead of in a vault. |
| `--tools` | Comma-separated tool list (used with `-H`). |

## What Gets Created

```
<vault>/skills/<name>/
  artifact.md    # the skill content file
```

The `artifact.md` file is pre-populated with YAML frontmatter:

```markdown
---
description: "your description"
---

# <name>

Your skill instructions here.
```

## Slash Syntax

Slash syntax (`art cr s/<name>`) is consistent across `cr`, `ed`, `cat`, `inspect`, `export`, and `ls`.
