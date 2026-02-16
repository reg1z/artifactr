## ADDED Requirements

### Requirement: Force flag on store command
The `store` command SHALL accept a `-f`/`--force` flag that overwrites existing artifacts in the target vault without prompting for confirmation. The interactive selection menu SHALL still be displayed.

#### Scenario: Store with force flag overwrites existing
- **WHEN** user runs `art store ./my-dir --force` and selects artifacts that already exist in the vault
- **THEN** the command SHALL overwrite the existing artifacts without prompting for confirmation

#### Scenario: Force flag preserves selection menu
- **WHEN** user runs `art store ./my-dir --force`
- **THEN** the interactive artifact selection menu SHALL still be displayed

#### Scenario: Store without force flag unchanged
- **WHEN** user runs `art store ./my-dir` without `--force`
- **THEN** the command SHALL prompt for confirmation before overwriting existing artifacts
