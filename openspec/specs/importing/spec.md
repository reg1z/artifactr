## Requirements

### Requirement: Supported tools
Artifactr MUST support `claude-code` and `opencode` as import targets.

#### Scenario: Modular tool support
- **WHEN** a new tool needs to be supported
- **THEN** tool support MUST be implemented using a modular/extensible pattern (base class) where each tool adapter defines the tool's name/identifier and destination paths for each artifact type

#### Scenario: Tool adapter reads from vault
- **WHEN** a tool adapter performs an import
- **THEN** it reads from the same tool-agnostic vault structure and writes to tool-specific destinations

### Requirement: Import mapping
Import sources and destinations MUST follow defined mappings.

#### Scenario: Source paths from vault
- **WHEN** artifacts are imported from a vault
- **THEN** sources are:
  - skills from `vault/skills/`
  - agents from `vault/agents/`
  - commands from `vault/commands/`

#### Scenario: Claude-code destinations
- **WHEN** importing for claude-code
- **THEN** destinations are `.claude/skills/`, `.claude/agents/`, `.claude/commands/` in the target repo

#### Scenario: OpenCode destinations
- **WHEN** importing for opencode
- **THEN** destinations are `.opencode/skills/`, `.opencode/agents/`, `.opencode/commands/` in the target repo

#### Scenario: Multi-tool fan-out
- **WHEN** the same artifact is imported for multiple tools
- **THEN** the single vault source is copied to each tool's destination independently

### Requirement: Import command
The `art import` command imports artifacts from a vault into a target git repository.

#### Scenario: Basic import
- **WHEN** `art import <target>` is run
- **THEN** all artifacts from the default vault are imported to the target repo for all supported tools

#### Scenario: Vault selection
- **WHEN** `--vault=<name-or-path>` is provided
- **THEN** artifacts are imported from that vault instead of the default

#### Scenario: Tool filtering
- **WHEN** `--tools=<tool1,tool2>` is provided
- **THEN** artifacts are only imported for the specified tools

#### Scenario: Missing target
- **WHEN** no target is provided and `--global` is not set
- **THEN** display error: `Error: No target git repo specified!`

#### Scenario: Non-git target
- **WHEN** target does not contain a `.git` directory
- **THEN** display error: `Error: Target is not a git repository!`

#### Scenario: Invalid vault
- **WHEN** the specified vault does not exist in the catalog
- **THEN** display error: `Error: Specified vault does not exist.`

#### Scenario: Invalid tools
- **WHEN** unsupported tools are specified
- **THEN** display error: `Error: Tools specified are not supported.`

#### Scenario: Multiple validation errors
- **WHEN** multiple validation errors occur simultaneously
- **THEN** all errors MUST be displayed in a single message

#### Scenario: Overwrite confirmation
- **WHEN** a file already exists at the destination
- **THEN** the user MUST be prompted: `File already exists: <path>\nOverwrite? [y/N]:`

#### Scenario: Symlink mode
- **WHEN** `--link` or `-l` is provided
- **THEN** artifacts are symlinked instead of copied

### Requirement: Git exclude management
Imported artifacts MUST be hidden from git tracking.

#### Scenario: Exclude file update
- **WHEN** artifacts are imported into a git repo
- **THEN** all imported paths MUST be added to `.git/info/exclude`

#### Scenario: No duplicate excludes
- **WHEN** an exclude pattern already exists in `.git/info/exclude`
- **THEN** it MUST NOT be added again

### Requirement: Selective import
The `--artifacts` flag allows importing individual artifacts by name.

#### Scenario: Named artifact import
- **WHEN** `--artifacts=name1,name2` is provided
- **THEN** only those artifacts are imported (not the full vault)

#### Scenario: Whitespace trimming
- **WHEN** artifact names contain whitespace around commas
- **THEN** whitespace MUST be trimmed

#### Scenario: Unique name resolution
- **WHEN** an artifact name is unique across all types
- **THEN** it is imported without further qualification

#### Scenario: Ambiguous name resolution
- **WHEN** an artifact name exists in multiple types and no type prefix is given
- **THEN** the user MUST be prompted to select one option

#### Scenario: Type-prefixed name
- **WHEN** `--artifacts=skills/write-thing` is provided with a type prefix
- **THEN** only that specific type is searched

#### Scenario: Name not found
- **WHEN** an artifact name is not found in the vault
- **THEN** an error is printed for that artifact and remaining artifacts continue processing

#### Scenario: Flag combinations
- **WHEN** `--artifacts` is combined with `--vault`, `--tools`, or `--link`
- **THEN** all flags MUST work together correctly

### Requirement: Import cache tracking
A `.art-cache/imported` file MUST track which artifacts have been imported.

#### Scenario: Cache creation
- **WHEN** artifacts are imported
- **THEN** `.art-cache/` is created in the target directory if it doesn't exist, and `.art-cache/imported` is created or updated

#### Scenario: Cache line format
- **WHEN** an import record is written
- **THEN** each line uses: `<vault-name-or-basename>.<tool-name>.<artifact-name>`

#### Scenario: Multi-tool tracking
- **WHEN** one artifact is imported for multiple tools
- **THEN** a separate line is written for each tool

#### Scenario: No duplicate lines
- **WHEN** the exact same import line already exists
- **THEN** it MUST NOT be written again

#### Scenario: Cache excluded from git
- **WHEN** `.art-cache/` is created
- **THEN** it MUST be added to `.git/info/exclude`

### Requirement: Global import
The `--global` / `-g` flag imports artifacts into a tool's user-wide global config directories.

#### Scenario: Global destination mapping
- **WHEN** `--global` is used
- **THEN** destinations are:
  - claude-code: `~/.claude/{skills,agents,commands}`
  - opencode: `~/.config/opencode/{skills,agents,commands}`

#### Scenario: Target becomes optional
- **WHEN** `--global` is used
- **THEN** the `target` positional argument is optional and ignored if provided

#### Scenario: Git operations skipped
- **WHEN** `--global` is used
- **THEN** no `.git/info/exclude` management, no git repo validation

#### Scenario: Global import tracking
- **WHEN** `--global` is used
- **THEN** imports are tracked in `~/.config/artifactr/.art-cache-global/imported` instead of a local `.art-cache/imported`

#### Scenario: Missing directory prompt
- **WHEN** a global config directory does not exist
- **THEN** the user is prompted: `Directory does not exist: <path>\nCreate it? [y/N]:`. If declined, that directory is skipped.

#### Scenario: Flag compatibility
- **WHEN** `--global` is combined with `--tools`, `--vault`, `--artifacts`, or `--link`
- **THEN** all flags MUST work together correctly

### Requirement: Force overwrite
The `--force` / `-f` flag skips per-file overwrite confirmations during import.

#### Scenario: Silent overwrite
- **WHEN** `--force` is used and a destination file exists
- **THEN** the file is overwritten without prompting

#### Scenario: Import-only scope
- **WHEN** `--force` is used
- **THEN** it applies only to `art import`, not to `art store`

#### Scenario: Directory creation not affected
- **WHEN** `--force` and `--global` are both used
- **THEN** the directory creation prompt from `--global` is still shown (force only controls file-level overwrites)

#### Scenario: Accurate reporting
- **WHEN** `--force` is used
- **THEN** the import summary still reports counts accurately (overwritten files count as imported)
