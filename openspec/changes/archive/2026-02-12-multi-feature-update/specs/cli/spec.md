## ADDED Requirements

### Requirement: Vault init subcommand
The CLI MUST register an `art vault init` subcommand.

#### Scenario: Vault init arguments
- **WHEN** `art vault init` is parsed
- **THEN** argparse MUST accept:
  - Positional: `target_dir` (required) - path to the vault directory
  - `--name` - optional name for the vault
  - `--set-default` - set the initialized vault as default

### Requirement: Edit command
The CLI MUST register an `art edit` subcommand.

#### Scenario: Edit arguments
- **WHEN** `art edit` is parsed
- **THEN** argparse MUST accept:
  - Positional: `artifact_type` (required) - one of `skill`, `agent`, `command`
  - Positional: `artifact_name` (required) - the artifact identifier
  - `--vault` - target vault (name or path)
  - `-H` / `--here` - edit in current project instead of vault
  - `--tools` - comma-separated tool list (used with `--here`)

### Requirement: Create command subcommand
The CLI MUST register an `art create command` sub-subcommand.

#### Scenario: Create command arguments
- **WHEN** `art create command` is parsed
- **THEN** argparse MUST accept:
  - Positional: `command_name` (required) - the command identifier / filename
  - `-d` / `--description` - command description (required for creation)
  - `-c` / `--content` - markdown body content
  - `-D` / `--field` - arbitrary frontmatter key=value (repeatable, `action="append"`)
  - `-H` / `--here` - create in current project instead of vault
  - `--vault` - target vault (name or path)
  - `--tools` - comma-separated tool list (used with `--here`)

### Requirement: Create agent subcommand
The CLI MUST register an `art create agent` sub-subcommand.

#### Scenario: Create agent arguments
- **WHEN** `art create agent` is parsed
- **THEN** argparse MUST accept:
  - Positional: `agent_name` (required) - the agent identifier
  - `-d` / `--description` - agent description (required for creation)
  - `-c` / `--content` - markdown body content
  - `-D` / `--field` - arbitrary frontmatter key=value (repeatable, `action="append"`)
  - `-H` / `--here` - create in current project instead of vault
  - `--vault` - target vault (name or path)
  - `--tools` - comma-separated tool list (used with `--here`)

### Requirement: Vault add set-default flag
The CLI MUST register a `--set-default` flag on the `art vault add` subcommand.

#### Scenario: Set-default flag
- **WHEN** `art vault add` is parsed
- **THEN** argparse MUST accept `--set-default` as a boolean flag

## MODIFIED Requirements

### Requirement: CLI framework
The CLI MUST be implemented using Python's `argparse` module.

#### Scenario: Argparse usage
- **WHEN** the CLI is built
- **THEN** `argparse` is used for all argument parsing with subcommands for each top-level command

#### Scenario: Decoupled logic
- **WHEN** CLI handlers are implemented
- **THEN** program logic MUST be decoupled from CLI invocations to allow for future GUI/TUI development

#### Scenario: Create subcommand
- **WHEN** the CLI is built
- **THEN** an `art create` subcommand is registered with `skill`, `command`, and `agent` sub-subcommands

#### Scenario: Create skill arguments
- **WHEN** `art create skill` is parsed
- **THEN** argparse accepts:
  - Positional: `name` (required) — the skill identifier / directory name
  - `-n` / `--name` — override the frontmatter display name
  - `-d` / `--description` — skill description
  - `-c` / `--content` — markdown body content
  - `-D` / `--field` — arbitrary frontmatter key=value (repeatable, `action="append"`)
  - `-H` / `--here` — create in current project instead of vault
  - `--vault` — target vault (name or path)
  - `--tools` — comma-separated tool list (used with `--here`)

### Requirement: Tool selection
Commands that operate on tools MUST support selecting specific tools or defaulting.

#### Scenario: Default tool
- **WHEN** no `--tools` flag is provided
- **THEN** the default tool is used

#### Scenario: Tool list
- **WHEN** `art tool list` is run
- **THEN** all supported tools are displayed with the current default indicated and aliases shown in parentheses

#### Scenario: Tool select
- **WHEN** `art tool select <tool-name>` is run
- **THEN** the default tool is updated (aliases MUST be resolved before validation)

### Requirement: Error handling
All errors MUST follow consistent conventions.

#### Scenario: Error output
- **WHEN** an error occurs
- **THEN** it MUST be displayed to stderr

#### Scenario: User-friendly errors
- **WHEN** an error is displayed
- **THEN** it MUST be user-friendly and actionable

#### Scenario: Exit codes
- **WHEN** a command fails
- **THEN** the CLI MUST exit with a non-zero status code

#### Scenario: EOFError handling
- **WHEN** a user prompt encounters `EOFError`
- **THEN** it MUST be handled gracefully by defaulting to "no action" (skip/cancel)

#### Scenario: No vault error guidance
- **WHEN** a command requires a vault and no default vault is set
- **THEN** the error MUST suggest both `art vault add` and `art vault init` as options
