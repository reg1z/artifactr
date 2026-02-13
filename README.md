# Artifactr

A cross-platform CLI tool for managing AI project artifacts. Maintain a personal library of skills, agents, and commands in centralized "vaults" and import them into any git repository for use with AI coding assistants.

## *Why?* 🤔
AI coding agents accumulate configs — skills, agents, commands — and they're usually project-local. Starting a new repo often means rebuilding your environment from scratch.

I develop mostly in cloud VMs via `ssh` and `tmux` for security purposes. I got tired of rebuilding my setup every time and desperately wanted a *terminal-centric* solution. Lo-and-behold: **Artifactr**

It takes inspiration from local-first note-taking applications like Obsidian and Logseq. No external connections are made. Your vaults contain YOUR files.

## Features

- **Tool-agnostic storage**: Store artifacts once, import to multiple AI tools
- **Cross-platform**: Works on Linux, macOS, and Windows
- **Multiple vaults**: Organize artifacts into separate collections with auto-naming (`llm-vault-N`)
- **Vault initialization**: Create new vaults from scratch with `art vault init`
- **Artifact creation**: Create skills, commands, and agents from the CLI with `art create`
- **Artifact editing**: Open artifacts in your terminal editor with `art edit`
- **Selective import**: Import specific artifacts by name with `--artifacts`
- **Artifact discovery**: Scan any project for existing artifacts with `art spelunk`
- **Artifact collection**: Store discovered artifacts back into a vault with `art store`
- **Import tracking**: `.art-cache/imported` records what was imported and from where
- **Supported tools**: Claude Code, OpenCode (extensible for more)
- **Automatic git exclusion**: Adds imported artifacts to `.git/info/exclude` to protect against accidental commits of project-specific skills & prompts


## Installation

Requires Python 3.10+

It's easiest to globally install `artifactr` via `pipx`:
```sh
pipx install artifactr
```

Otherwise, you can install via `pip` (though it's recommended to use a non-system venv):
```sh
pip install artifactr
```

## Quickstart
```sh
art vault add ~/my-vault
art store ~/repos/existing-project
art import ~/repos/new-project
```


## Usage

### Managing Vaults

```sh
# Initialize a new vault (creates directory with skills/, agents/, commands/ scaffolding)
art vault init ~/my-vault

# Initialize with a name and set as default
art vault init ~/my-vault --name=favorites --set-default

# Add an existing directory as a vault (auto-named as llm-vault-1, llm-vault-2, etc.)
art vault add ~/my-vault

# Add a vault with an explicit name
art vault add ~/my-vault --name=favorites

# Add and set as default in one step
art vault add ~/my-vault --name=favorites --set-default

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

Vaults added without `--name` are automatically assigned names using the `llm-vault-N` pattern. Vault names can be used in place of full directory paths in any command that accepts a vault identifier, including `--vault` on `art import`.

### Managing Tools

```sh
# List supported tools and see current default (shows aliases too)
art tool list

# Set default tool (defaults to opencode)
art tool select claude-code

# Aliases work anywhere a tool name is accepted
art tool select claude  # resolves to claude-code
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

### Creating Artifacts

Create skills, commands, and agents directly from the CLI:

```sh
# Create a skill (directory-based, with SKILL.md)
art create skill my-skill -d "A helpful skill" -c "Instructions here"

# Create a command (flat .md file, filename is the name)
art create command deploy-prod -d "Run production deployment"

# Create an agent (flat .md file, name in frontmatter)
art create agent code-reviewer -d "Reviews code changes"

# Add extra frontmatter fields
art create agent my-agent -d "desc" -D model=sonnet -D version=1.0

# Create in a specific vault
art create skill my-skill -d "desc" --vault=favorites

# Create in the current project instead of a vault
art create command my-cmd -d "desc" --here
art create skill my-skill -d "desc" --here --tools=claude-code,opencode
```

All artifact types require `--description` / `-d`. Skills are created as directories with a `SKILL.md` file; commands and agents are created as flat `.md` files.

### Editing Artifacts

Open an artifact in your terminal editor:

```sh
# Edit a skill in the default vault
art edit skill my-skill

# Edit a command or agent
art edit command deploy-prod
art edit agent code-reviewer

# Edit in a specific vault
art edit skill my-skill --vault=favorites

# Edit a project-local artifact
art edit skill my-skill --here
```

The editor is resolved from `$VISUAL`, then `$EDITOR`, then the first available of `nano`, `nvim`, `vim`, `vi`.

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
