## MODIFIED Requirements

### Requirement: Project import vault selection
`art proj import` MUST support multi-vault `-V` to import from multiple vaults.

#### Scenario: Import from single vault
- **WHEN** `art proj import -V favorites` is run
- **THEN** artifacts MUST be imported from `favorites` vault

#### Scenario: Import from multiple vaults
- **WHEN** `art proj import -V vault1,vault2` is run
- **THEN** artifacts from both `vault1` and `vault2` MUST be imported

#### Scenario: Import from multiple vaults (repeatable)
- **WHEN** `art proj import -V vault1 -V vault2` is run
- **THEN** it MUST behave identically to `-V vault1,vault2`

#### Scenario: Import without vault flag
- **WHEN** `art proj import` is run without `-V`
- **THEN** artifacts MUST be imported from the default vault (existing behavior)

### Requirement: Config import vault selection
`art conf import` MUST support multi-vault `-V` to import from multiple vaults.

#### Scenario: Config import from single vault
- **WHEN** `art conf import -V favorites` is run
- **THEN** artifacts MUST be imported from `favorites` vault

#### Scenario: Config import from multiple vaults
- **WHEN** `art conf import -V vault1,vault2` is run
- **THEN** artifacts from both `vault1` and `vault2` MUST be imported

#### Scenario: Config import without vault flag
- **WHEN** `art conf import` is run without `-V`
- **THEN** artifacts MUST be imported from the default vault (existing behavior)
