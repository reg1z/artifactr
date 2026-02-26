---
description: Context about Artifactr — what it is, how it's configured, vault structure, artifact types, and tool resolution.
version: 0.1
---

# Artifactr Context

Artifactr (`art`) is a local-first CLI tool for managing AI coding agent artifacts (skills, commands, agents) across projects. Users store artifacts in named **vaults**, then import them into any project as copies or symlinks.

## Config File Location

| Platform | Path |
|---|---|
| Linux / XDG | `~/.config/artifactr/config.yaml` |
| macOS | `~/Library/Application Support/artifactr/config.yaml` |
| Windows | `%APPDATA%/artifactr/config.yaml` |

## config.yaml Fields

```yaml
vaults:                    # list of absolute paths to registered vault directories
  - /home/user/my-vault
default_vault: /home/user/my-vault   # absolute path to the currently selected vault (null if unset)
default_tool: claude-code  # which tool's directory layout to use by default
vault_names:               # mapping of vault path → human name
  /home/user/my-vault: personal
tools: {}                  # custom tool definitions (overrides built-ins per tool name)
nav_mode: null             # optional navigation mode setting
```

## Finding the Default Vault

The `default_vault` key in `config.yaml` holds the **absolute path** to the currently selected vault. Run `art vault list` to see all registered vaults and which is default. Run `art vault select <name>` to change it.

## Vault Directory Structure

```
my-vault/
  vault.yaml        # per-vault metadata
  skills/           # one subdirectory per skill, each containing artifact.md
    my-skill/
      artifact.md
  commands/         # flat .md files
    my-command.md
  agents/           # flat .md files
    my-agent.md
```

## vault.yaml Fields

```yaml
name: personal     # vault display name
tools: {}          # optional per-vault tool overrides (same format as global tools)
```

## Artifact Types and File Formats

| Type | Format | Location in vault |
|---|---|---|
| **skill** | Directory containing `artifact.md` | `skills/<name>/` |
| **command** | Single `.md` file | `commands/<name>.md` |
| **agent** | Single `.md` file | `agents/<name>.md` |

Skills use a directory-per-skill layout because Claude Code and OpenCode expect that format. Commands and agents are flat markdown files.

## Three-Tier Tool Resolution

Tool definitions control which directories artifacts are read from and written to. Resolution order (higher tiers override lower tiers for the same tool name):

1. **Built-in tools** — default definitions for known tools (e.g., `claude-code`, `opencode`)
2. **Global config tools** — `tools:` dict in `~/.config/artifactr/config.yaml`
3. **Vault tools** — `tools:` dict in the vault's `vault.yaml`

A tool definition dict looks like:

```yaml
claude-code:
  aliases: [claude]
  skills: .claude/skills
  commands: .claude/commands
  agents: .claude/agents
  global_skills: $HOME/.claude/skills
  global_commands: $HOME/.claude/commands
  global_agents: $HOME/.claude/agents
```

Paths are repo-relative for local fields and support `$HOME` / `~` expansion for global fields.

## Common Commands

```sh
art vault list                   # list all registered vaults
art vault add <path>             # register a vault
art vault init <path>            # create and register a new vault
art vault select <name>          # set default vault
art proj import                  # import artifacts from vault into current project
art proj spelunk                 # discover artifacts in current project
art conf import                  # import into global tool config dirs
art update-native-skills         # install built-in skill files into current project
art uns -g                       # install built-in skills globally
art config backup                # backup all vaults to a zip archive
art config restore backup.zip    # restore vaults from a backup archive
```
