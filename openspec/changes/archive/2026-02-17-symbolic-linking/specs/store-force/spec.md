## ADDED Requirements

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
