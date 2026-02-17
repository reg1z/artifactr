## MODIFIED Requirements

### Requirement: Vault initialization
The `art vault init <target_dir>` command MUST create a new vault directory with the standard artifact subdirectories, register it in the catalog, and optionally name it and set it as default.

#### Scenario: New directory creation with prompt
- **WHEN** `art vault init /path/to/new-vault` is run and the directory does not exist
- **THEN** the user MUST be prompted: "Directory '/path/to/new-vault' does not exist. Create it? [Y/n]"
- **AND** if confirmed, the directory MUST be created with `skills/`, `agents/`, and `commands/` subdirectories, and the vault MUST be registered in the catalog
- **AND** if declined, the command MUST abort without creating anything

#### Scenario: New directory creation with --yes
- **WHEN** `art vault init /path/to/new-vault --yes` is run and the directory does not exist
- **THEN** the directory MUST be created without prompting

#### Scenario: Existing directory (idempotent)
- **WHEN** `art vault init /path/to/existing-dir` is run and the directory already exists
- **THEN** the vault MUST be registered in the catalog without modifying the existing directory contents (equivalent to `art vault add`)

#### Scenario: Named initialization
- **WHEN** `art vault init /path/to/vault --name=my-vault` is run
- **THEN** the vault MUST be registered with the name `my-vault`

#### Scenario: Auto-naming
- **WHEN** `art vault init /path/to/vault` is run without `--name`
- **THEN** the vault MUST be auto-named using the `vault-N` pattern (see vault add auto-naming requirement)

#### Scenario: Set default on init
- **WHEN** `art vault init /path/to/vault --set-default` is run
- **THEN** the initialized vault MUST be set as the default vault

#### Scenario: Already registered
- **WHEN** `art vault init /path/to/vault` is run and the vault is already in the catalog
- **THEN** the vault MUST be reported as already registered (same as `vault add` duplicate behavior)

#### Scenario: Informative output
- **WHEN** a vault is successfully initialized
- **THEN** output MUST include the vault name, location, and a hint for renaming: `To rename this vault: art vault name <name> <new-name>`

## ADDED Requirements

### Requirement: Vault init aliases
The `init` subcommand under `art vault` MUST accept `create` and `cr` as aliases.

#### Scenario: Using create alias
- **WHEN** `art vault create /path/to/dir` is run
- **THEN** the command MUST behave identically to `art vault init /path/to/dir`

#### Scenario: Using cr alias
- **WHEN** `art vault cr /path/to/dir` is run
- **THEN** the command MUST behave identically to `art vault init /path/to/dir`
