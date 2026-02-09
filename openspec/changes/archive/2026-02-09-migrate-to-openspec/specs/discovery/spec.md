## ADDED Requirements

### Requirement: Artifact probing logic
A shared probing mechanism MUST discover artifacts within a target directory by searching tool config directories.

#### Scenario: Config directory search
- **WHEN** a target directory is probed
- **THEN** only directories corresponding to supported tools' config directories are searched (`.claude/`, `.opencode/`)

#### Scenario: Skill detection
- **WHEN** searching `skills/` within a tool config directory
- **THEN** any subdirectory containing a `SKILL.md` file (case-sensitive) is detected as a skill artifact

#### Scenario: Agent detection
- **WHEN** searching `agents/` within a tool config directory
- **THEN** any `.md` file directly within is detected as an agent artifact

#### Scenario: Command detection
- **WHEN** searching `commands/` within a tool config directory
- **THEN** any `.md` file directly within is detected as a command artifact

### Requirement: Spelunk command
The `art spelunk <target>` command probes a target directory for existing artifacts and reports findings.

#### Scenario: Basic discovery
- **WHEN** `art spelunk <target>` is run on a directory with artifacts
- **THEN** a table is displayed with columns: NAME, TYPE, TOOL, DESCRIPTION

#### Scenario: Column formatting
- **WHEN** the output table is rendered
- **THEN** column widths are dynamically sized to fit the longest value with at least 2 spaces of padding between columns

#### Scenario: Artifact naming
- **WHEN** artifact names are displayed
- **THEN** skills use the directory name; agents and commands use the filename without extension

#### Scenario: Tool column
- **WHEN** the TOOL column is populated
- **THEN** it shows the tool derived from the config directory (e.g., `claude` for `.claude/`)

#### Scenario: Description from frontmatter
- **WHEN** the main artifact file contains YAML frontmatter with a non-empty `description` property
- **THEN** the description is shown; descriptions longer than 50 characters are truncated with `...`

#### Scenario: Missing description
- **WHEN** no valid frontmatter or description is found
- **THEN** the description column shows `-`

#### Scenario: Import detection
- **WHEN** an artifact's name matches an entry in `.art-cache/imported`
- **THEN** the NAME column appends `(imported: <vault-name>)`

#### Scenario: Multiple import sources
- **WHEN** an artifact matches multiple import entries from different vaults
- **THEN** all vault names are listed: `(imported: vault1, vault2)`

#### Scenario: Non-git target
- **WHEN** `art spelunk` is given a target that is not a git repo
- **THEN** it still works — no git repo validation required

#### Scenario: No artifacts found
- **WHEN** no tool config directories or artifacts are found
- **THEN** print: `No artifacts found in <target>`

#### Scenario: Target does not exist
- **WHEN** the target directory does not exist
- **THEN** print an error and exit with code 1

### Requirement: Store command
The `art store <target_dir>` command stores discovered artifacts from a project into a vault.

#### Scenario: Discovery and selection
- **WHEN** `art store <target_dir>` is run
- **THEN** artifacts are discovered using the shared probing logic, presented in a numbered list, and the user selects which to store

#### Scenario: Selection input formats
- **WHEN** the user enters a selection
- **THEN** the following formats are supported: individual numbers (`1`), comma-separated (`1,3,5`), ranges (`1-3`), the word `all`, and combinations (`1,3-5,7`)

#### Scenario: Vault selection
- **WHEN** `--vault=<name-or-path>` is provided
- **THEN** artifacts are stored into that vault; otherwise the default vault is used

#### Scenario: Storage mapping
- **WHEN** a selected artifact is stored
- **THEN** it is copied from the tool config directory to the vault's tool-agnostic structure:
  - `<target>/.claude/skills/my-skill/` → `<vault>/skills/my-skill/`
  - `<target>/.claude/agents/my-agent.md` → `<vault>/agents/my-agent.md`
  - `<target>/.opencode/commands/deploy.md` → `<vault>/commands/deploy.md`

#### Scenario: Overwrite confirmation
- **WHEN** an artifact with the same name already exists in the vault
- **THEN** the user MUST be prompted before overwriting

#### Scenario: No artifacts found
- **WHEN** no artifacts are discovered in the target
- **THEN** print: `No artifacts found in <target_dir>` and exit with code 0

#### Scenario: Invalid vault
- **WHEN** the specified vault does not exist in the catalog
- **THEN** print an error and exit with code 1

#### Scenario: Store confirmation
- **WHEN** artifacts are successfully stored
- **THEN** a confirmation is printed for each artifact, plus a summary count
