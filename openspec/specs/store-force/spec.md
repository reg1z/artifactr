## Requirements

### Requirement: Global store source
The `store` command MUST accept `--global`/`-g` to store artifacts from global tool configuration directories into a vault.

#### Scenario: Store from global config
- **WHEN** `art store --global` is run
- **THEN** artifacts from global tool configuration directories MUST be discovered and stored into the default vault

#### Scenario: Global with vault target
- **WHEN** `art store --global --vault favorites` is run
- **THEN** artifacts from global config MUST be stored into the `favorites` vault

#### Scenario: Global mutually exclusive with target_dir
- **WHEN** `art store ./some-dir --global` is run
- **THEN** an error MUST be displayed indicating that `--global` and a target directory cannot be used together

#### Scenario: Neither global nor target_dir
- **WHEN** `art store` is run without `--global` and without a target directory
- **THEN** an error MUST be displayed indicating that either a target directory or `--global` is required

### Requirement: Store tool filtering
The `store` command MUST accept `--tools` to filter which tools' artifacts are stored.

#### Scenario: Store with tools filter
- **WHEN** `art store --global --tools claude-code` is run
- **THEN** only artifacts from claude-code's global directories MUST be discovered and stored

#### Scenario: Store with multiple tools
- **WHEN** `art store ./some-dir --tools claude-code,opencode` is run
- **THEN** only artifacts from claude-code and opencode directories within `./some-dir` MUST be discovered and stored

#### Scenario: Tool alias resolution
- **WHEN** `art store --global --tools claude` is run
- **THEN** `claude` MUST be resolved to `claude-code` before filtering

### Requirement: Graceful skip for symlinked artifacts in store
`art store` MUST detect when a source artifact is a symlink pointing to the target vault and skip it gracefully.

#### Scenario: Source is symlink to target vault
- **WHEN** `art store` encounters a source artifact that is a symlink
- **AND** the symlink resolves to a path within the target vault
- **THEN** the artifact MUST be skipped with a message: "Skipping '<name>': already linked to this vault"

#### Scenario: Source is symlink to different vault
- **WHEN** `art store` encounters a source artifact that is a symlink
- **AND** the symlink resolves to a path outside the target vault
- **THEN** the artifact MUST be stored normally (content copied through the symlink)

#### Scenario: Source is not a symlink
- **WHEN** `art store` encounters a source artifact that is a regular file or directory
- **THEN** the existing store behavior MUST be unchanged
