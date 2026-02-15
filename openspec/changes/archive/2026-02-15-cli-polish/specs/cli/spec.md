## MODIFIED Requirements

### Requirement: Art list subcommand
The CLI MUST register an `art ls` subcommand at the top level.

#### Scenario: Art ls arguments
- **WHEN** `art ls` is parsed
- **THEN** argparse MUST accept:
  - `--vault` - target specific vault (name or path)
  - `-S`/`--skills` (`nargs='?'`) - filter to skills, optional names
  - `-C`/`--commands` (`nargs='?'`) - filter to commands, optional names
  - `-A`/`--agents` (`nargs='?'`) - filter to agents, optional names

### Requirement: Project namespace subcommand
The CLI MUST register a `project` subcommand with aliases `proj` and `p`.

#### Scenario: Project namespace arguments
- **WHEN** `art project`, `art proj`, or `art p` is parsed
- **THEN** it MUST expose subcommands: `import`, `rm`, `wipe`, `ls`

### Requirement: Config namespace subcommand
The CLI MUST register a `config` subcommand with aliases `conf` and `c`.

#### Scenario: Config namespace arguments
- **WHEN** `art config`, `art conf`, or `art c` is parsed
- **THEN** it MUST expose subcommands: `import`, `rm`, `wipe`, `ls`, `edit`

## ADDED Requirements

### Requirement: Vault namespace aliases
The CLI MUST register a `vault` subcommand with alias `v`.

#### Scenario: Vault alias
- **WHEN** `art v` is parsed
- **THEN** it MUST behave identically to `art vault`

### Requirement: Tool namespace aliases
The CLI MUST register a `tool` subcommand with alias `t`.

#### Scenario: Tool alias
- **WHEN** `art t` is parsed
- **THEN** it MUST behave identically to `art tool`

## RENAMED Requirements

### Requirement: Art list subcommand
- **FROM:** `art list`
- **TO:** `art ls`

### Requirement: Vault list subcommand
- **FROM:** `art vault list`
- **TO:** `art vault ls`

### Requirement: Tool list subcommand
- **FROM:** `art tool list`
- **TO:** `art tool ls`

### Requirement: Config list subcommand
- **FROM:** `art config list` / `art conf list`
- **TO:** `art config ls` / `art conf ls`

### Requirement: Project list subcommand
- **FROM:** `art project list` / `art proj list`
- **TO:** `art project ls` / `art proj ls`
