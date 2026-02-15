## MODIFIED Requirements

### Requirement: Config namespace registration
The CLI MUST register a `config` subcommand with aliases `conf` and `c` using argparse's `aliases` parameter. `art config <subcommand>`, `art conf <subcommand>`, and `art c <subcommand>` MUST all be accepted.

#### Scenario: Using full name
- **WHEN** `art config import` is run
- **THEN** it MUST be handled identically to `art conf import`

#### Scenario: Using alias
- **WHEN** `art conf import` is run
- **THEN** it MUST invoke the config import handler

#### Scenario: Using single-letter alias
- **WHEN** `art c import` is run
- **THEN** it MUST invoke the config import handler

### Requirement: Config list command
`art config ls` MUST display globally imported artifacts by reading `.art-cache-global/imported`.

#### Scenario: List all
- **WHEN** `art config ls` is run
- **THEN** all globally imported artifacts MUST be listed

#### Scenario: List with type filter
- **WHEN** `art config ls -S` is run
- **THEN** only globally imported skills MUST be shown

#### Scenario: List with tool filter
- **WHEN** `art config ls --tools opencode` is run
- **THEN** only artifacts imported for opencode MUST be shown

#### Scenario: List with no imports
- **WHEN** `art config ls` is run and no `.art-cache-global` exists
- **THEN** a message MUST be displayed indicating no imported artifacts were found

## ADDED Requirements

### Requirement: Config edit subcommand
The `config` namespace MUST expose an `edit` subcommand.

#### Scenario: Config edit registration
- **WHEN** `art config` help is displayed
- **THEN** `edit` MUST appear in the list of available subcommands
