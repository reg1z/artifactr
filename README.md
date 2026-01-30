# Artifactr

A cross-platform CLI tool for managing AI project artifacts. Maintain a personal library of prompts, skills, agents, and commands in centralized "vaults" and import them into any git repository for use with AI coding assistants.

## Features

- **Tool-agnostic storage**: Store artifacts once, import to multiple AI tools
- **Cross-platform**: Works on Linux, macOS, and Windows
- **Multiple vaults**: Organize artifacts into separate collections
- **Supported tools**: Claude Code, OpenCode (extensible for more)

## Installation

Requires Python 3.

```sh
pip install artifactr
```

## Usage

### Managing Vaults

```sh
# Add a vault
art vault add ~/my-vault

# List all vaults
art vault list

# Set default vault
art vault select ~/my-vault

# Remove a vault
art vault rm ~/my-vault
```

### Importing Artifacts

```sh
# Import all artifacts from default vault
art import ~/repos/my-project

# Import from a specific vault
art import ~/repos/my-project --vault=~/my-vault

# Import for specific tools only
art import ~/repos/my-project --tools=claude-code,opencode
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

Artifacts are copied to tool-specific directories in the target repo (e.g., `.claude/skills/`, `.opencode/agents/`) and automatically excluded from git tracking.
