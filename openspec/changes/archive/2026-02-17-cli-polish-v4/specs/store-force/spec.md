## MODIFIED Requirements

### Requirement: Store vault selection
`art store` MUST support multi-vault `-V` to store artifacts into multiple vaults.

#### Scenario: Store into single vault
- **WHEN** `art store ./dir -V favorites` is run
- **THEN** selected artifacts MUST be stored into `favorites` vault

#### Scenario: Store into multiple vaults
- **WHEN** `art store ./dir -V vault1,vault2` is run
- **THEN** selected artifacts MUST be stored into both `vault1` and `vault2` vaults

#### Scenario: Store into multiple vaults (repeatable)
- **WHEN** `art store ./dir -V vault1 -V vault2` is run
- **THEN** it MUST behave identically to `-V vault1,vault2`

#### Scenario: Store without vault flag
- **WHEN** `art store ./dir` is run without `-V`
- **THEN** artifacts MUST be stored into the default vault (existing behavior)

#### Scenario: Store confirmation per vault
- **WHEN** storing into multiple vaults
- **THEN** the confirmation and storage MUST proceed for each vault
