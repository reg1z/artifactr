---
plan: plans/artifactr_plan.md
---

# Artifactr Specification

## Overview

Artifactr is a cross-platform Python CLI tool for managing AI project artifacts. It allows users to maintain a personal library of prompts, skills, agents, and other AI tool configurations in centralized "vaults" and import them into target git repositories.

## Terminology

| Term | Definition |
|------|------------|
| **Artifact** | An individual skill, agent, command, or other configuration file stored in a vault |
| **Vault** | A user-specified directory containing artifacts in a tool-agnostic format, optionally identified by a name |
| **Catalog** | The collection of all registered vaults |
| **Vault Name** | An optional user-assigned alias for a vault, usable in place of its full directory path |
| **Tool** | An AI coding assistant (e.g., claude-code, opencode) that artifacts can be imported into |

## Requirements

### 1. Cross-Platform Compatibility

1.1. Artifactr MUST work on Linux, Windows, and macOS.

1.2. Artifactr MUST use platform-appropriate paths for configuration storage following XDG Base Directory Specification where applicable:
- **Linux**: `~/.config/artifactr/`
- **macOS**: `~/Library/Application Support/artifactr/`
- **Windows**: `%APPDATA%\artifactr\`

1.3. All file path operations MUST handle platform-specific path separators correctly.

### 2. Configuration Storage

2.1. Artifactr MUST store its configuration in a `config.yaml` file within the platform-specific config directory.

2.2. The configuration file MUST contain:
- `vaults`: A list of registered vault paths
- `default_vault`: Path to the current default vault (or `null` if none set)
- `vault_names`: A mapping of vault paths to their user-assigned names (may be empty)

### 3. Vault Structure

3.1. A vault MUST store artifacts in a **tool-agnostic** format. This means artifacts are stored once and can be imported into any supported tool without duplication.

3.2. A vault MUST follow this directory hierarchy:

```
vault/
├── skills/
│   └── skill-name/
│       ├── SKILL.md
│       └── (other files...)
├── agents/
│   └── agent-name.md
└── commands/
    └── command-name.md
```

3.3. Artifact types:
- **skills**: Directories containing a `SKILL.md` file and optional supporting files
- **agents**: Markdown files defining agent behavior
- **commands**: Markdown files defining custom commands

3.4. When importing, artifacts from this single source are copied to tool-specific destinations in the target repo. The same artifact can be imported for multiple tools without maintaining duplicate copies in the vault.

### 4. Supported Tools

4.1. Initial release MUST support:
- `claude-code`
- `opencode`

4.2. Tool support MUST be implemented using a modular/extensible pattern (base class or similar) to facilitate adding new tools later.

4.3. Each tool adapter MUST define:
- The tool's name/identifier
- The destination paths where each artifact type should be imported in a target repo

4.4. Tool adapters read from the same tool-agnostic vault structure (Section 3) and write to tool-specific destinations (Section 5).

### 5. Import Mapping

5.1. Import sources (from vault):
| Artifact Type | Source in Vault |
|---------------|-----------------|
| skills | `vault/skills/` |
| agents | `vault/agents/` |
| commands | `vault/commands/` |

5.2. Default import destinations for `claude-code`:
| Artifact Type | Destination in Target Repo |
|---------------|---------------------------|
| skills | `.claude/skills/` |
| agents | `.claude/agents/` |
| commands | `.claude/commands/` |

5.3. Default import destinations for `opencode`:
| Artifact Type | Destination in Target Repo |
|---------------|---------------------------|
| skills | `.opencode/skills/` |
| agents | `.opencode/agents/` |
| commands | `.opencode/commands/` |

5.4. Import flow example:
```
vault/skills/my-skill/  ──┬──>  repo/.claude/skills/my-skill/   (claude-code)
                          └──>  repo/.opencode/skills/my-skill/  (opencode)
```

5.5. Users MAY override default destinations via configuration.

### 6. CLI Interface

6.1. The CLI MUST be invoked using the command `art`.

6.2. The CLI MUST be implemented using Python's `argparse` module.

6.3. Program logic MUST be decoupled from CLI invocations to allow for future GUI development.

6.4. When no vault is explicitly specified, commands MUST use the default vault.

6.5. Any command that accepts a vault identifier MUST resolve it in the following order:
1. Exact resolved filesystem path
2. Vault name (from `vault_names`)
3. Directory basename match

6.6. Vault names MUST be unique across the catalog. Attempting to assign a name already in use by another vault MUST produce an error.

### 7. Commands

#### 7.1. `art import <target> [options]`

Imports artifacts from a vault into a target git repository.

**Arguments:**
- `target` (required): Path to the target git repository

**Options:**
- `--vault=<name-or-path>`: Use a specific vault instead of the default
- `--tools=<tool1,tool2,...>`: Import only artifacts for specified tools (comma-separated)

**Behavior:**

7.1.1. MUST validate that `target` is provided. If missing, display error: `Error: No target git repo specified!`

7.1.2. MUST validate that `target` is a git repository (contains a `.git` directory). If not, display error: `Error: Target is not a git repository!`

7.1.3. MUST validate that the specified vault exists in the catalog. If not, display error: `Error: Specified vault does not exist.`

7.1.4. MUST validate that all specified tools are supported. If any are not, display error: `Error: Tools specified are not supported.`

7.1.5. If multiple validation errors occur, MUST display all errors in a single message.

7.1.6. MUST copy artifact files from the vault to the target repo (not symlink).

7.1.7. When a file already exists at the destination, MUST prompt the user before overwriting:
```
File already exists: .claude/skills/my-skill/SKILL.md
Overwrite? [y/N]:
```

7.1.8. MUST add all imported paths to the target repo's `.git/info/exclude` file to prevent git tracking.

7.1.9. MUST NOT add duplicate entries to `.git/info/exclude`.

**Examples:**
```sh
# Import all artifacts from default vault
art import ~/repos/project

# Import from specific vault
art import ~/repos/project --vault=favorites

# Import only claude-code artifacts
art import ~/repos/project --tools=claude-code

# Import multiple tools from specific vault
art import ~/repos/project --vault=favorites --tools=claude-code,opencode
```

#### 7.2. `art vault add <path> [path...] [--name=<name>]`

Adds one or more directories to the vault catalog.

**Arguments:**
- `path` (required, multiple): One or more directory paths to add as vaults

**Options:**
- `--name=<name>`: Assign a name to the vault (only valid when adding a single vault)

**Behavior:**

7.2.1. MUST validate that each path exists and is a directory.

7.2.2. MUST NOT add duplicate vaults to the catalog.

7.2.3. If this is the first vault added, it MUST become the default vault automatically.

7.2.4. MUST display confirmation for each vault added.

7.2.5. If `--name` is provided with multiple paths, MUST display an error.

7.2.6. If `--name` is provided and the name is already in use, MUST display an error.

**Examples:**
```sh
# Add single vault
art vault add ~/Documents/my-vault

# Add a vault with a name
art vault add ~/Documents/my-vault --name=favorites

# Add multiple vaults
art vault add ~/Documents/favorites ~/Documents/work
```

#### 7.3. `art vault rm <identifier> [identifier...]`

Removes one or more vaults from the catalog.

**Arguments:**
- `identifier` (required, multiple): One or more vault names or paths to remove

**Behavior:**

7.3.1. MUST remove the specified vaults from the catalog.

7.3.2. If a removed vault was the default, MUST set `default_vault` to `null`.

7.3.3. MUST remove the vault's name from `vault_names` if one was assigned.

7.3.4. MUST display confirmation for each vault removed.

7.3.5. MUST display a warning if a specified vault is not in the catalog.

**Examples:**
```sh
# Remove by path
art vault rm ~/Documents/old-vault

# Remove by name
art vault rm favorites
```

#### 7.4. `art vault select <identifier>`

Sets a vault as the default.

**Arguments:**
- `identifier` (required): Name or path of the vault to set as default

**Behavior:**

7.4.1. MUST validate that the vault exists in the catalog (resolved per §6.5).

7.4.2. MUST update `default_vault` in the configuration.

7.4.3. MUST display confirmation of the new default.

**Examples:**
```sh
# Select by path
art vault select ~/Documents/favorites

# Select by name
art vault select favorites
```

#### 7.5. `art vault list`

Lists all vaults in the catalog.

**Arguments:** None

**Behavior:**

7.5.1. MUST display all vaults in the catalog.

7.5.2. MUST indicate which vault is the current default (e.g., with a `*` marker or `(default)` label).

7.5.3. If no vaults are registered, MUST display a helpful message.

7.5.4. Named vaults MUST display their name first, followed by the directory path in parentheses.

7.5.5. Unnamed vaults MUST display only their directory path.

**Example Output:**
```
Registered vaults:
  * favorites (/home/user/Documents/my-vault) (default)
    /home/user/Documents/work-vault
```

#### 7.6. `art vault name <identifier> <name>`

Sets or changes the name of a vault.

**Arguments:**
- `identifier` (required): Name or path of the vault to name
- `name` (required): The new name to assign

**Behavior:**

7.6.1. MUST validate that the vault exists in the catalog (resolved per §6.5).

7.6.2. MUST validate that the name is not already in use by another vault. Re-assigning the same name to the same vault is allowed (idempotent).

7.6.3. MUST update `vault_names` in the configuration.

7.6.4. MUST display confirmation of the assigned name.

**Examples:**
```sh
# Name a vault by its path
art vault name ~/Documents/my-vault favorites

# Rename a vault by its current name
art vault name favorites work
```

### 8. Error Handling

8.1. All errors MUST be displayed to stderr.

8.2. Errors MUST be user-friendly and actionable.

8.3. The CLI MUST exit with a non-zero status code on error.

### 9. Dependencies

9.1. Artifactr MUST only require Python 3.

9.2. Standard library modules to use:
- `argparse` for CLI parsing
- `pathlib` for cross-platform path handling
- `shutil` for file operations
- `os` and `platform` for system detection
