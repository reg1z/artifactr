## MODIFIED Requirements

### Requirement: Create artifact in vault
`art create <type> <name>` MUST support multi-vault `-V` to create the artifact in multiple vaults.

#### Scenario: Create in single vault
- **WHEN** `art create skill foo -V favorites` is run
- **THEN** the skill MUST be created in `favorites` vault only

#### Scenario: Create in multiple vaults
- **WHEN** `art create skill foo -V vault1,vault2` is run
- **THEN** the skill MUST be created in both `vault1` and `vault2` vaults

#### Scenario: Create without vault flag
- **WHEN** `art create skill foo` is run without `-V`
- **THEN** the skill MUST be created in the default vault (existing behavior)

#### Scenario: Create with --here flag
- **WHEN** `art create skill foo --here` is run with `-V vault1,vault2`
- **THEN** `-V` MUST be ignored since `--here` creates locally (existing behavior)
