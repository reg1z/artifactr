## ADDED Requirements

### Requirement: Tool add subcommand
The CLI MUST register an `art tool add` subcommand.

#### Scenario: Tool add arguments
- **WHEN** `art tool add` is parsed
- **THEN** argparse MUST accept:
  - Positional: `name` (required) - the tool identifier
  - `--skills` - repo-relative path for skills
  - `--commands` - repo-relative path for commands
  - `--agents` - repo-relative path for agents
  - `--global-skills` - absolute path for global skills
  - `--global-commands` - absolute path for global commands
  - `--global-agents` - absolute path for global agents
  - `--alias` - tool alias (repeatable, `action="append"`)
  - `--vault` - store in vault's metadata instead of global config
  - `-g` / `--global` - explicitly store in global config (default behavior)

### Requirement: Tool rm subcommand
The CLI MUST register an `art tool rm` subcommand.

#### Scenario: Tool rm arguments
- **WHEN** `art tool rm` is parsed
- **THEN** argparse MUST accept:
  - Positional: `name` (required) - the tool identifier to remove
  - `--vault` - remove from vault's metadata instead of global config
  - `-g` / `--global` - explicitly remove from global config (default behavior)

### Requirement: Tool show subcommand
The CLI MUST register an `art tool show` subcommand.

#### Scenario: Tool show arguments
- **WHEN** `art tool show` is parsed
- **THEN** argparse MUST accept:
  - Positional: `name` (required) - the tool identifier to display

## MODIFIED Requirements

### Requirement: Tool selection
Commands that operate on tools MUST support selecting specific tools or defaulting.

#### Scenario: Default tool
- **WHEN** no `--tools` flag is provided
- **THEN** the default tool is used

#### Scenario: Tool list
- **WHEN** `art tool list` is run
- **THEN** all tools (built-in, global config, vault) MUST be displayed in a table with columns: Name, Source, Skills, Commands, Agents, Aliases. The current default MUST be indicated.

#### Scenario: Tool select
- **WHEN** `art tool select <tool-name>` is run
- **THEN** the default tool is updated (aliases MUST be resolved before validation)

#### Scenario: Tool select custom tool
- **WHEN** `art tool select my-custom-tool` is run and `my-custom-tool` is defined in global config
- **THEN** the default tool MUST be set to `my-custom-tool`
