# Artifactr
I want to make a Artifactr, a tool written in python to manage AI project files like cursor rules, CLAUDE.md files, and other artifacts that are used in a git repo when using AI tools. It will also allow one to curate their own personal prompt library.

Lines marked with ⭐ are important.
## Core Features
- ⭐ Cross-compatible: Linux, Windows, and macos
- Manage a personal library of prompts & skills that one can easily import into a target git repo
	- This feature is implemented in a modular way that makes it easy to add support for other tools and formats
- ⭐Uses a tool–agnostic central store of "artifacts" that can be imported into most popular AI tools
- Local-first storage, like the note-taking app Obsidian
	- Reads files from user-specified directories
		- These directories are called "Vaults"
		- A user can specify and manage more than one vault
			- The list of all vaults is called the vault "Catalog"
		- By default, first directory a user specifies is the default
- Individual skills/agents/etc stored within a vault are called "Artifacts"
- Tools like claude-code, opencode, and amp are called "Tools"
- Import specified vault contents into a target git repo folder
	- The tool validates that a target directory is actually a git repo
	- Tool-specific contents can be precisely imported with the correct arguments.
	- There should NOT be any evidence of imported files / artifacts within the files/code tracked by git. The tool should automatically add imported files/folders to the git repo's `.git/info/exclude` file to facilitate this.
- CLI interface
	- To leave room for adding a GUI later, program logic is decoupled from CLI invocations.

## Dependencies
- Python 3

## Other Misc. Specs
- The CLI is invoked with `art`.
- When no extra arguments/flags are applied, will run commands using the user's default vault.

## Vault Hierarchy
```
- Vault
	- tool1
		- artifact-type1
			- artifact1
			- artifact2
			- …
		- artifact-type2
			- artifact1
			- …
	- tool2
		- …
```

## Importing
Importing into individual tools is dictated by that tool's configuration structure. This should be an extensible feature, such that it is easy to add support for other tools later on. Maybe using some kind of base class/interface or other form of template.

It should be easy for users to change the specific dirs per tool that artifacts are imported into using config file(s)

Rn we only want to focus on adding support for claude-code and opencode

### claude-code config structure
Relevant documentation is found at https://code.claude.com/docs/en/skills

The structure for skills within the claude-code tool vault subdirectory should look like this.

- Vault/
	- claude-code/
		- skills/
			- skill1/
				- SKILL.md
				- {other contents…}
				- reference.md
				- template.md
				- examples/
					- …
				- scripts/
					- …
			- …
		- agents
			- agent1.md
			- …
		- commands
			- comm1.md
			- …

## opencode tool dir
The same exact structure as claude.

## Commands

### import
Imports specified contents of vaults into a target git repo. Validates whether a target folder is actually a repo. If not, generates an error and notifies the user

Import all artifacts for every tool stored in the current default vault into the git repo at `~/repos/project`
```sh
art import ~/repos/project
```

Import all artifacts of the vault named "favorites" into the git repo at `~/repos/project`
```sh
art import ~/repos/project --vault=favorites
```

Import only artifacts of the "claude-code" tool into the git repo at `~/repos/project`.
```sh
art import ~/repos/project --tools=claude-code
```

Import only artifacts of the "claude-code" and "cursor" tools from the vault named "favorites" into the git repo at `~/repos/project`
```sh
art import ~/repos/project --vault=favorites --tools=claude-code,cursor
```

#### incorrect usage examples

##### No dir specified
Without any target, an error is generated. The user is notified.
```sh
art import
```

Output:
```
Error: No target git repo specified!
```

##### dir specified is not a git repo
```sh
art import ~/Documents
```

Output:
```
Error: Target is not a git repository!
```

##### Non-existent vaults/tools selected

When a vault that doesn't exist within the catalog and/or a tool that is not supported is listed, an error is generated. The user is notified.

example 1
```sh
art import ~/repos/project --vault=./non-existent
```

Output:
```
Error: Specified vault does not exist.
```

example 2
```sh
art import ~/repos/project --tools=asdftool,codex
```

Output:
```
Error: Tools specified are not supported.
```

example 3
```sh
art import ~/repos/project --tools=asdftool,codex --vault=./non-existent
```

Output:
```
Error: Specified vault does not exist. Tools specified are not supported.
```

### vault
Perform operations with vaults.

#### add
Add directories to the vault catalog. Takes an arbitrary amount of vaults

Add a target directory (`~/Documents/favorites`) to your catalog of vaults
```sh
art vault add ~/Documents/favorites
```

Add more than one target directory at once to your catalog of vaults
```sh
art vault add ~/Documents/favorites ~/Documents/work ~/Download/shared_vault
```

#### rm
Remove directories from the vault catalog.

```sh
art vault rm ~/Documents/favorites ~/Documents/work
```

#### select
Select a new default vault

```sh
art vault select ~/Download/shared_vault
```
