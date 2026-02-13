## ADDED Requirements

### Requirement: Tool info subcommand
The CLI MUST register an `art tool info` subcommand.

#### Scenario: Tool info arguments
- **WHEN** `art tool info` is parsed
- **THEN** argparse MUST accept:
  - Positional: `name` (optional, `nargs="?"`) - the tool identifier to display detail for. If omitted, shows the catalog view.
  - `--vault` (optional value, `nargs="?"`, `const=True`, `default=None`) - filter to a specific vault's tools. When provided without a value, filters to the default vault. When provided with a value, filters to that vault (resolved by name or path).
  - `-g` / `--global` (`action="store_true"`) - filter to global config tools only

### Requirement: Tool list vault flag
The `art tool list` subcommand MUST accept a `--vault` flag.

#### Scenario: Tool list with vault flag
- **WHEN** `art tool list --vault=team-vault` is parsed
- **THEN** the specified vault's tools MUST be used in resolution instead of the default vault's tools

## MODIFIED Requirements

### Requirement: Tool selection
Commands that operate on tools MUST support selecting specific tools or defaulting.

#### Scenario: Default tool
- **WHEN** no `--tools` flag is provided
- **THEN** the default tool is used

#### Scenario: Tool list
- **WHEN** `art tool list` is run
- **THEN** all resolved tools (built-in, global config, default vault) MUST be displayed in a table with columns: Name, Source, Skills, Commands, Agents, Aliases. The current default MUST be indicated.

#### Scenario: Tool select
- **WHEN** `art tool select <tool-name>` is run
- **THEN** the default tool is updated (aliases MUST be resolved before validation). Tool resolution MUST include the default vault's tools.

#### Scenario: Tool select custom tool
- **WHEN** `art tool select my-custom-tool` is run and `my-custom-tool` is defined in a vault or global config
- **THEN** the default tool MUST be set to `my-custom-tool`

## REMOVED Requirements

### Requirement: Tool show subcommand
**Reason**: Replaced by `art tool info` subcommand which provides both single-tool detail view and comprehensive catalog view.
**Migration**: Use `art tool info <name>` instead of `art tool show <name>`.
