# Artifactr

A cross-platform CLI tool inspired by Obsidian for managing AI project artifacts. Maintain a personal library of prompts, skills, agents, and commands in centralized "vaults" and import them into any git repository for use with AI coding assistants.


## Features

- **Tool-agnostic storage**: Store artifacts once, import to multiple AI tools
- **Cross-platform**: Works on Linux, macOS, and Windows
- **Multiple vaults**: Organize artifacts into separate collections with optional names
- **Supported tools**: Claude Code, OpenCode (extensible for more)
- **Automatic git exclusion**: Adds imported artifacts to `.git/info/exclude' to protect against accidental commits of project-specific skills & prompts


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
```

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
