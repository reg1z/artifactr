## ADDED Requirements

### Requirement: Config backup subcommand registration
The `config` namespace MUST expose a `backup` subcommand. `art config backup` and `art conf backup` MUST both be accepted.

#### Scenario: Backup subcommand visible
- **WHEN** `art config --help` is displayed
- **THEN** `backup` MUST appear in the list of available subcommands

#### Scenario: Alias routes to backup
- **WHEN** `art conf backup` is run
- **THEN** it MUST be handled identically to `art config backup`

#### Scenario: Optional output argument
- **WHEN** `art config backup` is parsed
- **THEN** it MUST accept an optional positional argument for the output file path

### Requirement: Config restore subcommand registration
The `config` namespace MUST expose a `restore` subcommand. `art config restore` and `art conf restore` MUST both be accepted.

#### Scenario: Restore subcommand visible
- **WHEN** `art config --help` is displayed
- **THEN** `restore` MUST appear in the list of available subcommands

#### Scenario: Alias routes to restore
- **WHEN** `art conf restore` is run
- **THEN** it MUST be handled identically to `art config restore`

#### Scenario: Required archive argument
- **WHEN** `art config restore` is parsed
- **THEN** it MUST require a positional argument for the backup archive path
