## ADDED Requirements

### Requirement: Base command description
The `art` parser description MUST be "Manage AI artifacts across multiple configurations, tools, & repositories."

#### Scenario: Help output description
- **WHEN** `art --help` is run
- **THEN** the description "Manage AI artifacts across multiple configurations, tools, & repositories." MUST appear

### Requirement: Custom help formatter
The `art` parser MUST use a custom formatter class that suppresses the auto-generated subparser listing and provides a custom usage line.

#### Scenario: Usage line format
- **WHEN** `art --help` is run
- **THEN** the usage line MUST read `usage: art [-h] [--version] <command> [<args>]`

#### Scenario: No auto-generated subparser list
- **WHEN** `art --help` is run
- **THEN** the default argparse "positional arguments" group listing subcommands MUST NOT appear

### Requirement: Categorized command groups in epilog
The `art` parser epilog MUST display commands grouped into categories.

#### Scenario: Vault Operations category
- **WHEN** `art --help` is run
- **THEN** the epilog MUST contain a "Vault Operations:" section listing `ls`, `rm`, `store`, `edit`, and `create` with brief descriptions

#### Scenario: Namespaces category
- **WHEN** `art --help` is run
- **THEN** the epilog MUST contain a "Namespaces:" section listing `vault`, `tool`, `project`, and `config` with their aliases shown in parentheses and brief descriptions

#### Scenario: Discovery category
- **WHEN** `art --help` is run
- **THEN** the epilog MUST contain a "Discovery:" section listing `spelunk` with a brief description

### Requirement: Default-targeting documentation
The `art --help` output MUST document default-targeting behavior.

#### Scenario: Vault/tool default note
- **WHEN** `art --help` is run
- **THEN** the output MUST include a note that commands target the active vault/tool by default, referencing `art vault select` and `art tool select`

### Requirement: Subcommand help descriptions
Every registered subcommand and sub-subcommand MUST have a non-empty `help=` string in its `add_parser()` call.

#### Scenario: Top-level subcommands
- **WHEN** any top-level subcommand's `add_parser()` is registered
- **THEN** it MUST include a `help=` parameter with a brief informative description

#### Scenario: Nested subcommands
- **WHEN** any nested subcommand (e.g., `art vault add`, `art tool select`) is registered
- **THEN** it MUST include a `help=` parameter with a brief informative description

### Requirement: Project targeting documentation
The `art project --help` output MUST document that the current working directory is targeted by default.

#### Scenario: Project help note
- **WHEN** `art project --help` is run
- **THEN** the description MUST note that commands target the current directory unless `--target` is specified
