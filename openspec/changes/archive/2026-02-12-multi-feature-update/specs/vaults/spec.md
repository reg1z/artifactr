## ADDED Requirements

### Requirement: Vault add auto-naming
When a vault is added without an explicit `--name` flag, it MUST be automatically assigned a name using the `llm-vault-N` pattern.

#### Scenario: First auto-named vault
- **WHEN** `art vault add /path/to/dir` is run without `--name` and no `llm-vault-*` names exist
- **THEN** the vault MUST be named `llm-vault-1`

#### Scenario: Incrementing counter
- **WHEN** `art vault add /path/to/dir` is run without `--name` and `llm-vault-3` is the highest existing auto-name
- **THEN** the vault MUST be named `llm-vault-4`

#### Scenario: Counter scans all vault names
- **WHEN** auto-naming occurs
- **THEN** the system MUST scan all values in `vault_names` for names matching `llm-vault-\d+` and pick `max(N) + 1`

#### Scenario: Informative auto-name output
- **WHEN** a vault is auto-named
- **THEN** output MUST include the assigned name, the vault path, and a hint: `To rename this vault: art vault name <assigned-name> <new-name>`

#### Scenario: Multiple vaults added without name
- **WHEN** `art vault add /path/one /path/two` is run without `--name`
- **THEN** each vault MUST receive a unique auto-name (e.g., `llm-vault-1` and `llm-vault-2`)

### Requirement: Vault add set-default flag
The `art vault add` command MUST support a `--set-default` flag.

#### Scenario: Set default on add
- **WHEN** `art vault add /path/to/dir --set-default` is run
- **THEN** the added vault MUST be set as the default vault, overriding any existing default

#### Scenario: Set default without flag
- **WHEN** `art vault add /path/to/dir` is run without `--set-default` and a default already exists
- **THEN** the existing default MUST NOT be changed

## MODIFIED Requirements

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
- **THEN** an error MUST be displayed with actionable guidance: the error MUST mention the path of the vault currently using that name and suggest using `art vault name` to rename it

#### Scenario: Invalid path
- **WHEN** a path does not exist or is not a directory
- **THEN** validation fails for that path

#### Scenario: Duplicate vault
- **WHEN** a vault is already in the catalog
- **THEN** it MUST NOT be added again

#### Scenario: First vault becomes default
- **WHEN** the first vault is added to an empty catalog
- **THEN** it MUST automatically become the default vault
