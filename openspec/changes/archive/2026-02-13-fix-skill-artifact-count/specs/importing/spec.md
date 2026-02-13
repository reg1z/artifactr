## MODIFIED Requirements

### Requirement: Import command
The `art import` command imports artifacts from a vault into a target git repository.

#### Scenario: Basic import
- **WHEN** `art import <target>` is run
- **THEN** all artifacts from the default vault are imported to the target repo for the current default tool, limited to artifact types the tool supports.

#### Scenario: Vault selection
- **WHEN** `--vault=<name-or-path>` is provided
- **THEN** artifacts are imported from that vault instead of the default

#### Scenario: Tool filtering
- **WHEN** `--tools=<tool1,tool2>` is provided
- **THEN** artifacts are only imported for the specified tools; tool aliases MUST be resolved before validation

#### Scenario: Tool alias in import
- **WHEN** `art import <target> --tools=claude` is run
- **THEN** `claude` MUST be resolved to `claude-code` and the import MUST proceed normally

#### Scenario: Partial tool import
- **WHEN** `art import <target> --tools=codex` is run and the vault contains skills, commands, and agents
- **THEN** only skills MUST be imported (codex only supports skills); commands and agents MUST be silently skipped

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
- **WHEN** unsupported tools are specified (after alias resolution)
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

#### Scenario: Vault tool definitions loaded
- **WHEN** an import uses a specific vault that has `vault.yaml` with tool definitions
- **THEN** those vault tool definitions MUST participate in tool resolution with highest precedence

#### Scenario: Artifact count for directory-based artifacts
- **WHEN** a skill directory containing multiple files is imported
- **THEN** the import result MUST count it as exactly 1 artifact, not as the number of files within the directory

#### Scenario: Artifact count for file-based artifacts
- **WHEN** a single-file artifact (agent or command) is imported
- **THEN** the import result MUST count it as exactly 1 artifact

#### Scenario: Artifact count in global import
- **WHEN** `art import --global` imports a skill directory containing multiple files
- **THEN** the import result MUST count it as exactly 1 artifact
