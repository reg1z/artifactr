## MODIFIED Requirements

### Requirement: Vault add auto-naming
When a vault is added without an explicit `--name` flag, it MUST be automatically assigned a name using the `vault-N` pattern.

#### Scenario: First auto-named vault
- **WHEN** `art vault add /path/to/dir` is run without `--name` and no `vault-*` names exist
- **THEN** the vault MUST be named `vault-1`

#### Scenario: Incrementing counter
- **WHEN** `art vault add /path/to/dir` is run without `--name` and `vault-3` is the highest existing auto-name
- **THEN** the vault MUST be named `vault-4`

#### Scenario: Counter scans all vault names
- **WHEN** auto-naming occurs
- **THEN** the system MUST scan all values in `vault_names` for names matching `vault-\d+` and pick `max(N) + 1`

#### Scenario: Informative auto-name output
- **WHEN** a vault is auto-named
- **THEN** output MUST include the assigned name, the vault path, and a hint: `To rename this vault: art vault name <assigned-name> <new-name>`

#### Scenario: Multiple vaults added without name
- **WHEN** `art vault add /path/one /path/two` is run without `--name`
- **THEN** each vault MUST receive a unique auto-name (e.g., `vault-1` and `vault-2`)
