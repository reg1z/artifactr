---
description: How to create a new Artifactr agent using `art cr a <name>`.
version: 0.2
---

# Creating Agents with Artifactr

An **agent** is a flat `.md` file artifact stored in `agents/<name>.md` inside a vault. Agents define sub-agent personas or specialized instruction sets for AI coding tools.

## Basic Usage

```sh
art cr a <name> -d 'description text'
```

The `-d` flag (description) is required. Slash syntax is also supported: `art cr a/<name>`.

### Command & Type Aliases

| Full | Shortest |
|---|---|
| `art create agent` | `art cr a` |

## Examples

```sh
art cr a code-reviewer -d 'Reviews pull requests'
art cr a code-reviewer -d 'PR reviewer' -V work                    # target vault "work"
art cr a code-reviewer -d 'Reviewer' -c 'You review code…'         # with body content
art cr a code-reviewer -d 'Reviewer' -n 'Code Reviewer'            # custom display name
art cr a code-reviewer -d 'Local agent' -H                         # create in CWD project, not vault
art cr a code-reviewer -d 'Reviewer' -D version=1.0 -D author=Jo   # create with additional frontmatter field(s)
art cr a code-reviewer -d 'Reviewer' --tools claude-code,opencode  # create in tool(s) config
```

## Flags

| Flag | Description |
|---|---|
| `-d`, `--description` | **Required.** Agent description (populates frontmatter `description:`). |
| `-c`, `--content` | Markdown body content placed after the frontmatter block. |
| `-n`, `--name` | Override the frontmatter display name (defaults to the identifier). |
| `-D`, `--field` | Additional frontmatter field as `key=value`. Repeatable. |
| `-V`, `--vault` | Target vault (name or path). Comma-separated or repeatable. Defaults to the configured default vault. |
| `-H`, `--here` | Create in the current project directory instead of in a vault. |
| `--tools` | Comma-separated tool list (used with `-H`). |

## What Gets Created

```
<vault>/agents/<name>.md    # the agent content file
```

The file is pre-populated with YAML frontmatter:

```md
---
description: "your description"
---

Your agent instructions here.
```

## Slash Syntax

Slash syntax (`art cr a/<name>`) is consistent across `cr`, `ed`, `cat`, `inspect`, `export`, and `ls`.
