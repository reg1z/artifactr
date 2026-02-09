## Requirements

### Requirement: Vault add
The `art vault add` command adds one or more directories to the vault catalog.

#### Scenario: Single vault add
- **WHEN** `art vault add <path>` is run with a valid directory
- **THEN** the vault is added to the catalog and confirmation is displayed

#### Scenario: Multiple vault add
- **WHEN** `art vault add <path1> <path2>` is run
- **THEN** each valid vault is added and confirmed individually

#### Scenario: Named vault add
- **WHEN** `--name=<name>` is provided with a single path
- **THEN** the vault is added with the given name

#### Scenario: Name with multiple paths
- **WHEN** `--name` is provided with multiple paths
- **THEN** an error MUST be displayed

#### Scenario: Duplicate name
- **WHEN** `--name` specifies a name already in use by another vault
- **THEN** an error MUST be displayed

#### Scenario: Invalid path
- **WHEN** a path does not exist or is not a directory
- **THEN** validation fails for that path

#### Scenario: Duplicate vault
- **WHEN** a vault is already in the catalog
- **THEN** it MUST NOT be added again

#### Scenario: First vault becomes default
- **WHEN** the first vault is added to an empty catalog
- **THEN** it MUST automatically become the default vault

### Requirement: Vault remove
The `art vault rm` command removes one or more vaults from the catalog.

#### Scenario: Remove by path or name
- **WHEN** `art vault rm <identifier>` is run
- **THEN** the matching vault is removed and confirmation is displayed

#### Scenario: Remove default vault
- **WHEN** the removed vault was the default
- **THEN** `default_vault` MUST be set to `null`

#### Scenario: Remove named vault
- **WHEN** a removed vault had a name
- **THEN** the name MUST be removed from `vault_names`

#### Scenario: Vault not found
- **WHEN** the specified vault is not in the catalog
- **THEN** a warning MUST be displayed

### Requirement: Vault select
The `art vault select` command sets a vault as the default.

#### Scenario: Select by identifier
- **WHEN** `art vault select <identifier>` is run with a valid vault
- **THEN** `default_vault` is updated and confirmation is displayed

#### Scenario: Invalid vault
- **WHEN** the identifier does not match any vault in the catalog
- **THEN** validation fails

### Requirement: Vault list
The `art vault list` command lists all vaults in the catalog.

#### Scenario: Basic listing
- **WHEN** `art vault list` is run
- **THEN** all vaults are displayed with the default marked using `*` prefix and `(default)` label

#### Scenario: Named vault display
- **WHEN** a vault has a name
- **THEN** the name is shown first, followed by the path in parentheses

#### Scenario: Unnamed vault display
- **WHEN** a vault has no name
- **THEN** only the directory path is displayed

#### Scenario: Empty catalog
- **WHEN** no vaults are registered
- **THEN** a helpful message MUST be displayed

### Requirement: Vault list hierarchy
The `--all` / `-a` flag displays the full vault hierarchy with artifacts.

#### Scenario: Hierarchy display
- **WHEN** `art vault list --all` is run
- **THEN** output shows a tree-style hierarchy:
  - Level 1: Vault name (or path if unnamed)
  - Level 2: Artifact type headings (`skills/`, `agents/`, `commands/`) — only if that type has artifacts
  - Level 3: Individual artifact names (trailing `/` for skill directories)

#### Scenario: Skill display
- **WHEN** a skill directory exists in the vault
- **THEN** its directory name is shown with a trailing `/`; internal contents are NOT shown

#### Scenario: Missing vault path
- **WHEN** a vault's directory no longer exists on disk
- **THEN** it is still listed but with `(path not found)` next to the name

#### Scenario: Empty vault
- **WHEN** a vault has no artifact directories
- **THEN** it appears in the list with no children

### Requirement: Vault name
The `art vault name` command sets or changes the name of a vault.

#### Scenario: Assign name
- **WHEN** `art vault name <identifier> <name>` is run
- **THEN** `vault_names` is updated and confirmation is displayed

#### Scenario: Idempotent rename
- **WHEN** the same name is re-assigned to the same vault
- **THEN** the operation succeeds (idempotent)

#### Scenario: Name collision
- **WHEN** the name is already in use by a different vault
- **THEN** an error MUST be displayed

#### Scenario: Vault not found
- **WHEN** the identifier does not match any vault
- **THEN** validation fails
