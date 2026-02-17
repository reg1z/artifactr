## ADDED Requirements

### Requirement: Project link command
`art proj link` MUST be registered as a subcommand of the `project` namespace with alias `ln`.

#### Scenario: Command registration
- **WHEN** `art proj --help` is displayed
- **THEN** `link` MUST appear in the list of available subcommands

#### Scenario: Alias registration
- **WHEN** `art proj ln` is run
- **THEN** it MUST invoke the project link handler

#### Scenario: Positional arguments
- **WHEN** `art proj link name1 name2` is run
- **THEN** `name1` and `name2` MUST be parsed as artifact names (nargs='*')

#### Scenario: All flag
- **WHEN** `art proj link --all` or `art proj link -a` is run
- **THEN** the `all` flag MUST be set to True

#### Scenario: Force flag
- **WHEN** `art proj link --force` or `art proj link -f` is run
- **THEN** the `force` flag MUST be set to True

#### Scenario: Vault flag — single vault
- **WHEN** `art proj link --vault favorites` or `art proj link -V favorites` is run
- **THEN** the operation MUST be scoped to artifacts imported from `favorites` only

#### Scenario: Vault flag — multiple vaults (comma-separated)
- **WHEN** `art proj link -V vault1,vault2` is run
- **THEN** the operation MUST be scoped to artifacts imported from both `vault1` and `vault2`

#### Scenario: Vault flag — multiple vaults (repeatable)
- **WHEN** `art proj link -V vault1 -V vault2` is run
- **THEN** it MUST behave identically to `-V vault1,vault2`

#### Scenario: No vault flag (default)
- **WHEN** `art proj link -a` is run without `--vault`
- **THEN** the operation MUST be scoped to the currently selected default vault

#### Scenario: Type filter flags
- **WHEN** `art proj link -S` is run
- **THEN** only skill artifacts MUST be targeted

### Requirement: Project unlink command
`art proj unlink` MUST be registered as a subcommand of the `project` namespace with alias `uln`.

#### Scenario: Command registration
- **WHEN** `art proj --help` is displayed
- **THEN** `unlink` MUST appear in the list of available subcommands

#### Scenario: Alias registration
- **WHEN** `art proj uln` is run
- **THEN** it MUST invoke the project unlink handler

#### Scenario: Positional arguments
- **WHEN** `art proj unlink name1` is run
- **THEN** `name1` MUST be parsed as an artifact name

#### Scenario: All flag
- **WHEN** `art proj unlink --all` or `art proj unlink -a` is run
- **THEN** the `all` flag MUST be set to True

#### Scenario: Vault flag on unlink
- **WHEN** `art proj unlink -V favorites` is run
- **THEN** the operation MUST be scoped to artifacts imported from `favorites` only

#### Scenario: No vault flag on unlink (default)
- **WHEN** `art proj unlink -a` is run without `--vault`
- **THEN** the operation MUST be scoped to the currently selected default vault
