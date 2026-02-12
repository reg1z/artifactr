## ADDED Requirements

### Requirement: Vault initialization
The `art vault init <target_dir>` command MUST create a new vault directory with the standard artifact subdirectories, register it in the catalog, and optionally name it and set it as default.

#### Scenario: New directory creation
- **WHEN** `art vault init /path/to/new-vault` is run and the directory does not exist
- **THEN** the directory MUST be created with `skills/`, `agents/`, and `commands/` subdirectories, and the vault MUST be registered in the catalog

#### Scenario: Existing directory (idempotent)
- **WHEN** `art vault init /path/to/existing-dir` is run and the directory already exists
- **THEN** the vault MUST be registered in the catalog without modifying the existing directory contents (equivalent to `art vault add`)

#### Scenario: Named initialization
- **WHEN** `art vault init /path/to/vault --name=my-vault` is run
- **THEN** the vault MUST be registered with the name `my-vault`

#### Scenario: Auto-naming
- **WHEN** `art vault init /path/to/vault` is run without `--name`
- **THEN** the vault MUST be auto-named using the `llm-vault-N` pattern (see vault add auto-naming requirement)

#### Scenario: Set default on init
- **WHEN** `art vault init /path/to/vault --set-default` is run
- **THEN** the initialized vault MUST be set as the default vault

#### Scenario: Already registered
- **WHEN** `art vault init /path/to/vault` is run and the vault is already in the catalog
- **THEN** the vault MUST be reported as already registered (same as `vault add` duplicate behavior)

#### Scenario: Informative output
- **WHEN** a vault is successfully initialized
- **THEN** output MUST include the vault name, location, and a hint for renaming: `To rename this vault: art vault name <name> <new-name>`
