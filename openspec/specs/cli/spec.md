## ADDED Requirements

### Requirement: Art list subcommand
The CLI MUST register an `art list` subcommand at the top level.

#### Scenario: Art list arguments
- **WHEN** `art list` is parsed
- **THEN** argparse MUST accept:
  - `--vault` - target specific vault (name or path)
  - `-S`/`--skills` (`nargs='?'`) - filter to skills, optional names
  - `-C`/`--commands` (`nargs='?'`) - filter to commands, optional names
  - `-A`/`--agents` (`nargs='?'`) - filter to agents, optional names

### Requirement: Art rm subcommand
The CLI MUST register an `art rm` subcommand at the top level.

#### Scenario: Art rm arguments
- **WHEN** `art rm` is parsed
- **THEN** argparse MUST accept:
  - Positional: `names` (`nargs='+'`) - artifact names to remove (supports `type/name` prefix)
  - `--vault` - target specific vault
  - `-f`/`--force` - skip confirmation

### Requirement: Project namespace subcommand
The CLI MUST register a `project` subcommand with alias `proj`.

#### Scenario: Project namespace arguments
- **WHEN** `art project` or `art proj` is parsed
- **THEN** it MUST expose subcommands: `import`, `rm`, `wipe`, `list`

### Requirement: Config namespace subcommand
The CLI MUST register a `config` subcommand with alias `conf`.

#### Scenario: Config namespace arguments
- **WHEN** `art config` or `art conf` is parsed
- **THEN** it MUST expose subcommands: `import`, `rm`, `wipe`, `list`

### Requirement: Store type filter flags
The `art store` subcommand MUST accept type filter flags.

#### Scenario: Store type filter arguments
- **WHEN** `art store` is parsed
- **THEN** argparse MUST accept `-S`/`--skills`, `-C`/`--commands`, `-A`/`--agents` with `nargs='?'`

### Requirement: Spelunk enhanced arguments
The `art spelunk` subcommand MUST accept enhanced arguments.

#### Scenario: Spelunk arguments
- **WHEN** `art spelunk` is parsed
- **THEN** argparse MUST accept:
  - Positional: `target` (`nargs='?'`) - optional, no default
  - `-g`/`--global` - explicit global config scanning
  - `--tools` - comma-separated tool filter
  - `-S`/`--skills`, `-C`/`--commands`, `-A`/`--agents` with `nargs='?'`

## REMOVED Requirements

### Requirement: Top-level import subcommand
**Reason**: Replaced by `art proj import` and `art conf import` namespaces.
**Migration**: Use `art proj import [target]` or `art conf import`.
