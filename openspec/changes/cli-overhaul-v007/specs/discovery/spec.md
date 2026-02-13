## MODIFIED Requirements

### Requirement: Artifact probing logic
A shared probing mechanism MUST discover artifacts within a target directory by searching tool config directories.

#### Scenario: Config directory search
- **WHEN** a target directory is probed and the target is not a vault
- **THEN** directories corresponding to all known tools' repo-local artifact paths MUST be searched (derived from tool definitions, not hardcoded)

#### Scenario: Partial tool probing
- **WHEN** probing for a tool that only supports skills
- **THEN** only the tool's skills path MUST be searched; commands and agents paths MUST be skipped

#### Scenario: Custom tool probing
- **WHEN** a custom tool is defined with `skills: .my-tool/skills`
- **THEN** `.my-tool/skills/` MUST be included in the probe search paths

#### Scenario: Skill detection
- **WHEN** searching a tool's skills path
- **THEN** any subdirectory containing a `SKILL.md` file (case-sensitive) is detected as a skill artifact

#### Scenario: Agent detection
- **WHEN** searching a tool's agents path
- **THEN** any `.md` file directly within is detected as an agent artifact

#### Scenario: Command detection
- **WHEN** searching a tool's commands path
- **THEN** any `.md` file directly within is detected as a command artifact

#### Scenario: Vault detection
- **WHEN** the target directory contains a `vault.yaml` file
- **THEN** the target MUST be treated as a vault and `skills/`, `commands/`, `agents/` directories MUST be scanned directly instead of tool config directories

#### Scenario: Type filter applied to discovery
- **WHEN** type filter flags are active during discovery
- **THEN** only artifact types matching the filter MUST be returned

## ADDED Requirements

### Requirement: Spelunk optional target with global default
The `spelunk` command's target argument MUST be optional. When no target is given, it MUST default to spelunking global config directories.

#### Scenario: No target provided
- **WHEN** `art spelunk` is run without a target
- **THEN** global config directories for all configured tools MUST be scanned
- **AND** output MUST indicate that global config is being spelunked by default because no target was given

#### Scenario: Explicit global flag
- **WHEN** `art spelunk -g` or `art spelunk --global` is run
- **THEN** global config directories MUST be scanned (same behavior as no target, for clarity)

#### Scenario: Target provided
- **WHEN** `art spelunk /path/to/dir` is run
- **THEN** the specified directory MUST be scanned (existing behavior, enhanced with vault detection)

### Requirement: Spelunk tool filtering
The `spelunk` command MUST accept a `--tools` flag to filter which tools' directories are scanned.

#### Scenario: Tool filter with target
- **WHEN** `art spelunk /path --tools claude-code` is run
- **THEN** only claude-code's directories MUST be scanned in the target

#### Scenario: Tool filter with global
- **WHEN** `art spelunk --tools opencode` is run (no target)
- **THEN** only opencode's global directories MUST be scanned

#### Scenario: Tool alias in filter
- **WHEN** `art spelunk --tools claude` is run
- **THEN** `claude` MUST be resolved to `claude-code` before filtering

### Requirement: Spelunk type filtering
The `spelunk` command MUST accept `-S`/`--skills`, `-C`/`--commands`, `-A`/`--agents` type filter flags.

#### Scenario: Type filter on spelunk
- **WHEN** `art spelunk /path -S` is run
- **THEN** only skill artifacts MUST be listed

#### Scenario: Named type filter on spelunk
- **WHEN** `art spelunk /path -S foo,bar` is run
- **THEN** only skills named `foo` and `bar` MUST be listed

### Requirement: Global config directory scanning
A mechanism MUST exist to scan global config directories for installed artifacts.

#### Scenario: Scanning global paths
- **WHEN** global config is spelunked
- **THEN** each tool's `global_skills`, `global_commands`, `global_agents` paths MUST be checked for artifacts

#### Scenario: Custom tool global paths
- **WHEN** a custom tool has `global_skills: /custom/path/skills`
- **THEN** `/custom/path/skills` MUST be included in the global scan

#### Scenario: Missing global directory
- **WHEN** a tool's global directory does not exist
- **THEN** it MUST be silently skipped (no error)
