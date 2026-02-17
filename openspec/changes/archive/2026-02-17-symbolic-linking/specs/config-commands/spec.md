## ADDED Requirements

### Requirement: Config link command
`art conf link` MUST be registered as a subcommand of the `config` namespace with alias `ln`.

#### Scenario: Command registration
- **WHEN** `art conf --help` is displayed
- **THEN** `link` MUST appear in the list of available subcommands

#### Scenario: Alias registration
- **WHEN** `art conf ln` is run
- **THEN** it MUST invoke the config link handler

#### Scenario: Positional arguments
- **WHEN** `art conf link name1 name2` is run
- **THEN** `name1` and `name2` MUST be parsed as artifact names (nargs='*')

#### Scenario: All flag
- **WHEN** `art conf link --all` or `art conf link -a` is run
- **THEN** the `all` flag MUST be set to True

#### Scenario: Force flag
- **WHEN** `art conf link --force` or `art conf link -f` is run
- **THEN** the `force` flag MUST be set to True

#### Scenario: Vault flag — scoping
- **WHEN** `art conf link -V vault1,vault2` or `art conf link -V vault1 -V vault2` is run
- **THEN** the operation MUST be scoped to artifacts imported from the specified vaults

#### Scenario: No vault flag (default)
- **WHEN** `art conf link -a` is run without `--vault`
- **THEN** the operation MUST be scoped to the currently selected default vault

### Requirement: Config unlink command
`art conf unlink` MUST be registered as a subcommand of the `config` namespace with alias `uln`.

#### Scenario: Command registration
- **WHEN** `art conf --help` is displayed
- **THEN** `unlink` MUST appear in the list of available subcommands

#### Scenario: Alias registration
- **WHEN** `art conf uln` is run
- **THEN** it MUST invoke the config unlink handler

#### Scenario: Positional arguments
- **WHEN** `art conf unlink name1` is run
- **THEN** `name1` MUST be parsed as an artifact name

#### Scenario: All flag
- **WHEN** `art conf unlink --all` or `art conf unlink -a` is run
- **THEN** the `all` flag MUST be set to True

#### Scenario: Vault flag on unlink
- **WHEN** `art conf unlink -V favorites` is run
- **THEN** the operation MUST be scoped to artifacts imported from `favorites` only

#### Scenario: No vault flag on unlink (default)
- **WHEN** `art conf unlink -a` is run without `--vault`
- **THEN** the operation MUST be scoped to the currently selected default vault
