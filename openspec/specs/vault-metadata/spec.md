## ADDED Requirements

### Requirement: vault.yaml file
Each vault MAY contain a `vault.yaml` file at its root directory. This file stores portable vault metadata.

#### Scenario: vault.yaml location
- **WHEN** a vault exists at `/path/to/my-vault`
- **THEN** its metadata file, if present, MUST be at `/path/to/my-vault/vault.yaml`

#### Scenario: vault.yaml is optional
- **WHEN** a vault directory does not contain `vault.yaml`
- **THEN** the vault MUST continue to function as before (no metadata, no vault-scoped tools)

### Requirement: Vault name in vault.yaml
The `vault.yaml` file MAY contain a `name` field that provides the vault's portable name.

#### Scenario: Name present
- **WHEN** `vault.yaml` contains `name: team-vault`
- **THEN** the vault's name MUST resolve to `team-vault`

#### Scenario: Name precedence over config.yaml
- **WHEN** `vault.yaml` contains `name: portable-name` and `config.yaml` `vault_names` maps the same vault to `local-name`
- **THEN** `vault.yaml` name MUST take precedence when displaying vault names

#### Scenario: No name in vault.yaml
- **WHEN** `vault.yaml` exists but has no `name` field
- **THEN** the vault name MUST fall back to `config.yaml` `vault_names` or the auto-generated name

### Requirement: Vault-scoped tool definitions
The `vault.yaml` file MAY contain a `tools:` section defining tool configurations scoped to that vault.

#### Scenario: Tools section format
- **WHEN** `vault.yaml` contains a `tools:` section
- **THEN** each entry MUST follow the same tool definition schema as user global config tools

#### Scenario: Vault tools loaded during operations
- **WHEN** an import or store operation uses a specific vault
- **THEN** that vault's `vault.yaml` tool definitions MUST be loaded and participate in tool resolution with highest precedence

#### Scenario: Vault tools do not leak
- **WHEN** vault A defines a custom tool and vault B is the active vault
- **THEN** vault A's tool definitions MUST NOT be visible

### Requirement: vault.yaml creation via art tool add
When `art tool add --vault=<name>` is used and the vault does not yet have a `vault.yaml`, the file MUST be created.

#### Scenario: First vault tool
- **WHEN** `art tool add my-tool --skills .t/skills --vault=team-vault` is run and `team-vault` has no `vault.yaml`
- **THEN** a new `vault.yaml` MUST be created with the tool definition under `tools:`

#### Scenario: Subsequent vault tool
- **WHEN** `art tool add another-tool --skills .a/skills --vault=team-vault` is run and `vault.yaml` already exists with other tools
- **THEN** the new tool MUST be added to the existing `tools:` section without disturbing other entries

### Requirement: Vault name written during vault init
When `art vault init` creates a vault with a `--name`, the name MUST be stored in `vault.yaml`.

#### Scenario: Init with name
- **WHEN** `art vault init ./my-vault --name=team-vault` is run
- **THEN** `vault.yaml` MUST be created at `./my-vault/vault.yaml` containing `name: team-vault`

#### Scenario: Init without name
- **WHEN** `art vault init ./my-vault` is run without `--name`
- **THEN** `vault.yaml` MAY be created with the auto-generated name, or not created at all (implementation choice)
