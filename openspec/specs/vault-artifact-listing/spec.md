## ADDED Requirements

### Requirement: Vault artifact list command
`art list` MUST display artifacts stored in a vault with their types and descriptions.

#### Scenario: List default vault contents
- **WHEN** `art list` is run without `--vault`
- **THEN** all artifacts in the default vault MUST be listed with columns: NAME, TYPE, DESCRIPTION

#### Scenario: List specific vault contents
- **WHEN** `art list --vault my-vault` is run
- **THEN** artifacts from the specified vault MUST be listed

#### Scenario: List with skills filter
- **WHEN** `art list -S` is run
- **THEN** only skill artifacts MUST be shown

#### Scenario: List with commands filter
- **WHEN** `art list -C` is run
- **THEN** only command artifacts MUST be shown

#### Scenario: List with agents filter
- **WHEN** `art list -A` is run
- **THEN** only agent artifacts MUST be shown

#### Scenario: List with named filter
- **WHEN** `art list -S foo,bar` is run
- **THEN** only skills named `foo` and `bar` MUST be shown

#### Scenario: List with multiple type filters
- **WHEN** `art list -S -C` is run
- **THEN** skills and commands MUST be shown; agents MUST be excluded

#### Scenario: Empty vault
- **WHEN** `art list` is run and the vault contains no artifacts
- **THEN** a message MUST indicate the vault is empty

#### Scenario: No default vault
- **WHEN** `art list` is run and no default vault is configured
- **THEN** an error MUST be displayed instructing the user to set up a vault

### Requirement: Vault artifact list description extraction
Each listed artifact MUST display its description from YAML frontmatter, truncated to 50 characters if necessary.

#### Scenario: Skill description
- **WHEN** a skill's `SKILL.md` has a `description` field in its YAML frontmatter
- **THEN** that description MUST be displayed (truncated with `...` if over 50 chars)

#### Scenario: Missing description
- **WHEN** an artifact has no `description` in its frontmatter
- **THEN** `-` MUST be displayed as the description
