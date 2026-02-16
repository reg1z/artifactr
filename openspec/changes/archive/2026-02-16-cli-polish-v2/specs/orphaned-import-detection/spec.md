## ADDED Requirements

### Requirement: Detect source-missing imports
When displaying artifacts in spelunk output, the system SHALL check whether each imported artifact still exists in its source vault. If the vault exists but the artifact is no longer present, the display SHALL append `source missing` to the import indicator.

#### Scenario: Artifact deleted from vault
- **WHEN** an artifact is in the import cache as imported from vault "my-vault"
- **AND** the vault "my-vault" exists and is registered
- **AND** the artifact no longer exists in "my-vault"
- **THEN** the spelunk output SHALL display `artifact-name (imported: my-vault, source missing)`

### Requirement: Detect vault-not-found imports
When displaying artifacts in spelunk output, the system SHALL check whether each source vault still exists. If the vault name cannot be resolved to a valid path, the display SHALL append `vault not found` to the import indicator.

#### Scenario: Vault no longer registered
- **WHEN** an artifact is in the import cache as imported from vault "old-vault"
- **AND** the vault "old-vault" is not in the vault catalog
- **THEN** the spelunk output SHALL display `artifact-name (imported: old-vault, vault not found)`

#### Scenario: Vault path no longer exists on disk
- **WHEN** an artifact is in the import cache as imported from vault "my-vault"
- **AND** the vault "my-vault" is registered but its path no longer exists on disk
- **THEN** the spelunk output SHALL display `artifact-name (imported: my-vault, vault not found)`

### Requirement: Healthy imports display unchanged
When an imported artifact's source vault and source artifact both exist, the display SHALL remain unchanged.

#### Scenario: Source exists
- **WHEN** an artifact is in the import cache as imported from vault "my-vault"
- **AND** the vault "my-vault" exists and the artifact still exists within it
- **THEN** the spelunk output SHALL display `artifact-name (imported: my-vault)` with no additional indicator
