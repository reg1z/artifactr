---
description: How to create a new Artifactr command using `art cr c <name>`.
version: 0.2
---

# Creating Commands with Artifactr

A **command** is a flat `.md` file artifact stored in `commands/<name>.md` inside a vault. Commands are concise, token-efficient instructions intended to be used as slash commands.

## Basic Usage

```sh
art cr c <name> -d 'description text'
```

The `-d` flag (description) is required. Slash syntax is also supported: `art cr c/<name>`.

### Command & Type Aliases

| Full | Shortest |
|---|---|
| `art create command` | `art cr c` |

## Examples

```sh
art cr c run-tests -d 'Run the test suite'
art cr c run-tests -d 'Run tests' -V work                # target vault "work"
art cr c run-tests -d 'Run tests' -c 'Execute pytest...' # with body content
art cr c run-tests -d 'Local cmd' -H                     # create in CWD project, not vault
art cr c run-tests -d 'Run tests' -D version=1.0 -D author=Jo         # create with additional frontmatter field(s)
art cr c run-tests -d 'Run tests' --tools claude-code,opencode         # create in tool(s) config
```

## Flags

| Flag | Description |
|---|---|
| `-d`, `--description` | **Required.** Command description (populates frontmatter `description:`). |
| `-c`, `--content` | Markdown body content placed after the frontmatter block. |
| `-D`, `--field` | Additional frontmatter field as `key=value`. Repeatable. |
| `-V`, `--vault` | Target vault (name or path). Comma-separated or repeatable. Defaults to the configured default vault. |
| `-H`, `--here` | Create in the current project directory instead of in a vault. |
| `--tools` | Comma-separated tool list (used with `-H`). |

## What Gets Created

```
<vault>/commands/<name>.md    # the command content file
```

The file is pre-populated with YAML frontmatter:

```markdown
---
description: "your description"
---

Your command instructions here.
```

## Slash Syntax

Slash syntax (`art cr c/<name>`) is consistent across `cr`, `ed`, `cat`, `inspect`, `export`, and `ls`.
