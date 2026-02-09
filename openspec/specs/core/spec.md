## Requirements

### Requirement: Cross-platform compatibility
Artifactr MUST work on Linux, Windows, and macOS. All file path operations MUST handle platform-specific path separators correctly.

#### Scenario: Platform-appropriate config directory
- **WHEN** Artifactr determines its configuration directory
- **THEN** it MUST use platform-appropriate paths:
  - Linux: `~/.config/artifactr/` (respecting `XDG_CONFIG_HOME` if set)
  - macOS: `~/Library/Application Support/artifactr/`
  - Windows: `%APPDATA%\artifactr\`

#### Scenario: Path separator handling
- **WHEN** any file path operation is performed
- **THEN** platform-specific path separators MUST be handled correctly

### Requirement: Configuration storage
Artifactr MUST store its configuration in a `config.yaml` file within the platform-specific config directory.

#### Scenario: Config file structure
- **WHEN** the configuration file is read or written
- **THEN** it MUST contain:
  - `vaults`: A list of registered vault paths
  - `default_vault`: Path to the current default vault (or `null` if none set)
  - `vault_names`: A mapping of vault paths to their user-assigned names (may be empty)
  - `default_tool`: The default tool identifier (defaults to first supported tool)

#### Scenario: Missing config file
- **WHEN** the config file does not exist
- **THEN** a default empty config MUST be returned: `{"vaults": [], "default_vault": null}`

#### Scenario: Config directory creation
- **WHEN** config is saved and the parent directory does not exist
- **THEN** the directory MUST be created automatically

### Requirement: Vault structure
A vault MUST store artifacts in a tool-agnostic format. Artifacts are stored once and can be imported into any supported tool without duplication.

#### Scenario: Vault directory hierarchy
- **WHEN** a vault is used for storage or import
- **THEN** it MUST follow this structure:
  - `vault/skills/` — directories containing a `SKILL.md` file and optional supporting files
  - `vault/agents/` — markdown files defining agent behavior
  - `vault/commands/` — markdown files defining custom commands

#### Scenario: Tool-agnostic import source
- **WHEN** artifacts are imported for multiple tools
- **THEN** the same vault source is used for all tools — no per-tool duplication in the vault

### Requirement: Terminology
The project MUST use consistent terminology.

#### Scenario: Term definitions
- **WHEN** referring to project concepts
- **THEN** the following terms apply:
  - **Artifact**: An individual skill, agent, command, or other configuration file stored in a vault
  - **Vault**: A user-specified directory containing artifacts in a tool-agnostic format, optionally identified by a name
  - **Catalog**: The collection of all registered vaults
  - **Vault Name**: An optional user-assigned alias for a vault, usable in place of its full directory path
  - **Tool**: An AI coding assistant (e.g., claude-code, opencode) that artifacts can be imported into
  - **Tool Config Directory**: The hidden folder in a project where a tool stores its config (e.g., `.claude/`)
  - **Art Cache**: A `.art-cache/` folder created in target directories to track imported artifacts

### Requirement: Dependencies
Artifactr MUST only require Python 3.

#### Scenario: Standard library usage
- **WHEN** Artifactr is built
- **THEN** it MUST use these standard library modules:
  - `argparse` for CLI parsing
  - `pathlib` for cross-platform path handling
  - `shutil` for file operations
  - `os` and `platform` for system detection

#### Scenario: External dependency
- **WHEN** YAML parsing is needed
- **THEN** the `PyYAML` library MUST be used (the only external dependency)
