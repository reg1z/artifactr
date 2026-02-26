## Requirements

### Requirement: Built-in skill files bundled with package
The package MUST include a `builtin_skills/` directory under `src/artifactr/` containing skill and command markdown files. This directory MUST be declared as package data so it is included in built wheels and accessible from any install method.

#### Scenario: Package data declared
- **WHEN** `pyproject.toml` is inspected
- **THEN** a `[tool.setuptools.package-data]` stanza MUST exist with `"artifactr" = ["builtin_skills/**/*"]`

#### Scenario: Accessible from PyPI install
- **WHEN** `importlib.resources.files("artifactr") / "builtin_skills"` is evaluated in any install context
- **THEN** the path MUST resolve to a readable directory containing skill and command files

### Requirement: Built-in skill directory structure
The `builtin_skills/` directory MUST contain a `skills/` subdirectory with one directory per skill and a `commands/` subdirectory with one `.md` file per paired command.

#### Scenario: Skills directory layout
- **WHEN** `builtin_skills/skills/` is listed
- **THEN** it MUST contain directories: `artifactr-context/`, `art-create-skill/`, `art-create-cmd/`, `art-create-agent/`

#### Scenario: Commands directory layout
- **WHEN** `builtin_skills/commands/` is listed
- **THEN** it MUST contain files: `art-create-skill.md`, `art-create-cmd.md`, `art-create-agent.md`

#### Scenario: Each skill directory has artifact file
- **WHEN** any skill directory under `builtin_skills/skills/` is opened
- **THEN** it MUST contain an `artifact.md` file

### Requirement: Built-in skill frontmatter
Every built-in skill `artifact.md` MUST contain a YAML frontmatter block. The frontmatter MUST include a `version` field with an initial value of `0.1`.

#### Scenario: Frontmatter version field present
- **WHEN** any built-in `artifact.md` is read
- **THEN** the YAML frontmatter MUST include `version: 0.1`

#### Scenario: Frontmatter description field present
- **WHEN** any built-in `artifact.md` is read
- **THEN** the YAML frontmatter MUST include a non-empty `description` field

### Requirement: artifactr-context skill content
The `artifactr-context` skill MUST document: what Artifactr is; the platform-specific location of `config.yaml` (Linux: `~/.config/artifactr/config.yaml`); all config.yaml fields (`vaults`, `default_vault`, `default_tool`, `vault_names`, `tools`, `nav_mode`); vault directory structure (`skills/`, `commands/`, `agents/` plus `vault.yaml`); `vault.yaml` fields (`name`, `tools`); artifact types and their file formats (skills are directories, commands and agents are `.md` files); how to find the default selected vault; and the three-tier tool resolution order.

#### Scenario: Config file location documented
- **WHEN** the `artifactr-context` skill content is read
- **THEN** it MUST describe `~/.config/artifactr/config.yaml` as the config file location on Linux/XDG

#### Scenario: Default vault resolution documented
- **WHEN** the `artifactr-context` skill content is read
- **THEN** it MUST explain that `default_vault` in `config.yaml` holds the absolute path to the currently selected default vault

#### Scenario: Artifact types documented
- **WHEN** the `artifactr-context` skill content is read
- **THEN** it MUST describe all three artifact types: skills (directories), commands (`.md` files), agents (`.md` files)

### Requirement: art-create-* skill content
Each `art-create-skill`, `art-create-cmd`, and `art-create-agent` skill MUST document the `art create` command syntax for its respective artifact type, including the slash syntax shorthand (`art create skill/<name>`).

#### Scenario: Slash syntax documented
- **WHEN** any `art-create-*` skill content is read
- **THEN** it MUST include an example using `art create <type>/<name>` syntax

#### Scenario: Paired command is token-minimal
- **WHEN** any `commands/art-create-*.md` file is read
- **THEN** it MUST be concise, containing only the essential `art create` invocation with minimal framing (no extended explanations)

### Requirement: `art update-native-skills` command
The CLI MUST register a top-level `update-native-skills` command with alias `uns`. Running it MUST copy built-in skill and command files from the package into the appropriate tool directories.

#### Scenario: Command and alias registered
- **WHEN** `art --help` is displayed
- **THEN** `update-native-skills` MUST appear in the subcommand list

#### Scenario: Alias works
- **WHEN** `art uns` is run
- **THEN** it MUST be handled identically to `art update-native-skills`

### Requirement: Local install target (default)
When run without `--global`, `art update-native-skills` MUST install skills into the CWD-relative tool directories (e.g., `.claude/skills/` for claude-code).

#### Scenario: Skills installed to CWD tool dir
- **WHEN** `art update-native-skills` is run in a CWD with the default tool configured
- **THEN** built-in skill directories MUST be copied into `<CWD>/<tool-skills-path>/`

#### Scenario: Commands installed to CWD tool dir
- **WHEN** `art update-native-skills` is run in a CWD with the default tool configured
- **THEN** built-in command `.md` files MUST be copied into `<CWD>/<tool-commands-path>/`

#### Scenario: Silently overwrites existing files
- **WHEN** a built-in skill already exists at the destination
- **THEN** it MUST be overwritten without prompting

### Requirement: Git repo confirmation for local install
When installing to CWD (not `--global`) and CWD is not a git repository, the command MUST prompt the user for confirmation before proceeding.

#### Scenario: Prompt shown outside git repo
- **WHEN** `art update-native-skills` is run in a directory that is not a git repo
- **THEN** a Y/n confirmation prompt MUST be displayed before any files are written

#### Scenario: No prompt inside git repo
- **WHEN** `art update-native-skills` is run in a directory that is a git repo
- **THEN** installation MUST proceed without any confirmation prompt

#### Scenario: Abort on negative confirmation
- **WHEN** the user responds `n` to the confirmation prompt
- **THEN** no files MUST be written and the command MUST exit with a non-zero code

### Requirement: Global install flag
`art update-native-skills` MUST support `-g`/`--global` to install into global tool config directories instead of CWD-relative paths.

#### Scenario: Global flag routes to global dirs
- **WHEN** `art uns -g` is run
- **THEN** built-in skills and commands MUST be copied into the global tool directories (e.g., `~/.claude/skills/`) for the default tool

#### Scenario: Global install skips git check
- **WHEN** `art uns -g` is run outside a git repo
- **THEN** no confirmation prompt MUST be shown

### Requirement: Tool selection flag for update-native-skills
`art update-native-skills` MUST support `--tools <tool1,tool2>` to install into specific tools' directories instead of the default tool only.

#### Scenario: Single tool override
- **WHEN** `art uns --tools claude-code` is run
- **THEN** skills and commands MUST be installed only into claude-code's directories

#### Scenario: Multiple tools
- **WHEN** `art uns --tools claude-code,opencode` is run
- **THEN** skills and commands MUST be installed into both tools' directories
