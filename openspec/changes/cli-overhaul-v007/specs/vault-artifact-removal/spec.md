## ADDED Requirements

### Requirement: Vault artifact rm command
`art rm <names...>` MUST remove artifacts from a vault.

#### Scenario: Remove from default vault
- **WHEN** `art rm foo` is run without `--vault`
- **THEN** the artifact named `foo` MUST be removed from the default vault

#### Scenario: Remove from specific vault
- **WHEN** `art rm foo --vault my-vault` is run
- **THEN** the artifact MUST be removed from the specified vault

#### Scenario: Remove with type-qualified name
- **WHEN** `art rm skills/foo` is run
- **THEN** only the skill named `foo` MUST be removed (no ambiguity)

#### Scenario: Ambiguous name
- **WHEN** `art rm foo` is run and `foo` exists as both a skill and a command in the vault
- **THEN** the user MUST be prompted to choose which artifact to remove

#### Scenario: Remove with confirmation
- **WHEN** `art rm foo` is run without `--force`
- **THEN** a confirmation prompt MUST be shown listing the artifact(s) that will be removed

#### Scenario: Remove with force
- **WHEN** `art rm foo -f` is run
- **THEN** the artifact MUST be removed without confirmation

#### Scenario: Multiple artifacts
- **WHEN** `art rm foo bar baz` is run
- **THEN** all named artifacts MUST be resolved and removed (with confirmation unless `--force`)

#### Scenario: Nonexistent artifact
- **WHEN** `art rm nonexistent` is run
- **THEN** an error MUST be displayed indicating the artifact was not found

#### Scenario: No default vault
- **WHEN** `art rm foo` is run and no default vault is configured
- **THEN** an error MUST be displayed instructing the user to set up a vault

### Requirement: Vault rm does not use type filter flags
`art rm` MUST NOT accept `-S`/`--skills`, `-C`/`--commands`, or `-A`/`--agents` flags. Type disambiguation MUST use the `type/name` prefix syntax or interactive prompts.

#### Scenario: Type filter flags rejected
- **WHEN** `art rm foo -S` is run
- **THEN** argparse MUST reject the flag as an unrecognized argument
