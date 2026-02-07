# Artifactr

A cross-platform CLI tool inspired by Obsidian for managing AI project artifacts. Maintain a personal library of prompts, skills, agents, and commands in centralized "vaults" and import them into any git repository for use with AI coding assistants.


## Features

- **Tool-agnostic storage**: Store artifacts once, import to multiple AI tools
- **Cross-platform**: Works on Linux, macOS, and Windows
- **Multiple vaults**: Organize artifacts into separate collections with optional names
- **Selective import**: Import specific artifacts by name with `--artifacts`
- **Artifact discovery**: Scan any project for existing artifacts with `art spelunk`
- **Artifact collection**: Store discovered artifacts back into a vault with `art store`
- **Import tracking**: `.art-cache/imported` records what was imported and from where
- **Supported tools**: Claude Code, OpenCode (extensible for more)
- **Automatic git exclusion**: Adds imported artifacts to `.git/info/exclude` to protect against accidental commits of project-specific skills & prompts


## Installation

Requires Python 3.

```sh
git clone https://github.com/reg1z/artifactr
cd artifactr
pip install .
```

## Usage

### Managing Vaults

```sh
# Add a vault
art vault add ~/my-vault

# Add a vault with a name
art vault add ~/my-vault --name=favorites

# Name or rename an existing vault
art vault name ~/my-vault favorites

# List all vaults
art vault list

# List all vaults with full artifact hierarchy
art vault list --all

# Set default vault (by name or path)
art vault select favorites

# Remove a vault (by name or path)
art vault rm favorites
```

Vault names can be used in place of full directory paths in any command that accepts a vault identifier, including `--vault` on `art import`.

### Managing Tools

```sh
# List supported tools and see current default
art tool list

# Set default tool (defaults to opencode)
art tool select claude-code
```

### Importing Artifacts

```sh
# Import artifacts from default vault to default tool
art import ~/repos/my-project

# Import from a specific vault (by name or path)
art import ~/repos/my-project --vault=favorites

# Import for specific tools (overrides default)
art import ~/repos/my-project --tools=claude-code,opencode

# Symlink artifacts instead of copying
art import ~/repos/my-project --link

# Import only specific artifacts by name
art import ~/repos/my-project --artifacts=helping-hand,code-review

# Combine with other flags
art import ~/repos/my-project --vault=favorites --artifacts=helping-hand --link
```

Imported artifacts are tracked in `.art-cache/imported` within the target directory, recording which vault and tool each artifact came from.

### Discovering Artifacts

Scan any directory for existing artifacts across all supported tool config directories:

```sh
# Discover artifacts in a project
art spelunk ~/repos/my-project
```

Example output:

```
NAME                              TYPE      TOOL      DESCRIPTION
helping-hand (imported: favs)     skill     claude    A helpful assistant
utility-tool                      skill     claude    -
reviewer                          agent     claude    Reviews code changes
deploy                            command   opencode  -
```

The `(imported: ...)` marker appears when an artifact was previously imported via `art import`, showing which vault it came from.

### Storing Artifacts

Collect artifacts from a project directory and store them into a vault:

```sh
# Store artifacts into default vault
art store ~/repos/my-project

# Store into a specific vault
art store ~/repos/my-project --vault=favorites
```

You'll be presented with a numbered list of discovered artifacts and can select which ones to store using individual numbers (`1`), ranges (`1-3`), comma-separated (`1,3,5`), combinations (`1,3-5`), or `all`.

## Vault Structure

```
vault/
├── skills/
│   └── skill-name/
│       ├── SKILL.md
│       └── (supporting files...)
├── agents/
│   └── agent-name.md
└── commands/
    └── command-name.md
```

Artifacts are copied (or symlinked with `--link`) to tool-specific directories in the target repo (e.g., `.claude/skills/`, `.opencode/agents/`) and automatically excluded from git tracking.
