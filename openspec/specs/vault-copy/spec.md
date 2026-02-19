## Purpose

Spec for `art vault copy` (`art vault cp`) — a command for cloning a vault's artifact directories and configuration to a new location and registering it.

## Requirements

### Requirement: art vault copy clones a vault
The `art vault copy` command MUST copy a vault's artifact directories and configuration to a new location and register the new vault.

#### Scenario: Explicit destination path
- **WHEN** `art vault copy my-vault /path/to/new-vault` is run
- **THEN** the contents of `my-vault` (see selective copy requirement below) MUST be copied to `/path/to/new-vault`
- **AND** the new vault MUST be registered in `config.yaml` automatically

#### Scenario: Name-only destination uses fallback location
- **WHEN** `art vault copy my-vault new-vault-name` is run and `new-vault-name` contains no path separator
- **THEN** the new vault MUST be created at `<config_dir>/vaults/<new-vault-name>/` where `<config_dir>` is the platform-appropriate config directory
- **AND** the new vault MUST be registered in `config.yaml` with the name `new-vault-name`

#### Scenario: Source vault identified by name or path
- **WHEN** the source argument matches a registered vault name
- **THEN** that vault's path MUST be used as the source
- **WHEN** the source argument is a filesystem path
- **THEN** that path MUST be used directly as the source

#### Scenario: Destination already exists — error
- **WHEN** the resolved destination path already exists
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1 without copying

### Requirement: art vault copy selective file inclusion
By default, `art vault copy` MUST copy only artifact directories and vault configuration.

#### Scenario: Default copy scope
- **WHEN** `art vault copy` is run without `--all`
- **THEN** ONLY the following MUST be copied: `skills/`, `commands/`, `agents/` subdirectories and `vault.yaml`
- **AND** any other files or directories in the vault root MUST be excluded

#### Scenario: --all includes additional files
- **WHEN** `art vault copy --all` is run (alias: `-a`)
- **THEN** ALL files and directories in the vault root MUST be copied, EXCEPT `.git/`
- **AND** the `.git/` directory MUST ALWAYS be excluded, even with `--all`

### Requirement: art vault copy preserves vault configuration
The copied vault MUST have its vault name updated but retain all other `vault.yaml` settings.

#### Scenario: Vault name updated in vault.yaml
- **WHEN** a vault is copied and a destination name is provided
- **THEN** the `name` field in the copied vault's `vault.yaml` MUST be set to the destination vault name
- **AND** all other fields in `vault.yaml` (e.g., custom tool definitions) MUST remain unchanged

#### Scenario: Vault name from directory when not specified
- **WHEN** no explicit name is provided (destination is a path, not a name)
- **THEN** the vault name in `vault.yaml` MUST be derived from the destination directory's basename

### Requirement: art vault copy aliases
The `art vault copy` command MUST be accessible via the alias `art vault cp`.

#### Scenario: art vault cp is equivalent to art vault copy
- **WHEN** `art vault cp` is run with any valid arguments
- **THEN** behavior MUST be identical to `art vault copy` with the same arguments
