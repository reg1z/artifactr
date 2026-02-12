## Requirements

### Requirement: CLI invocation
The CLI MUST be invoked using the command `art`.

#### Scenario: Entry point
- **WHEN** the package is installed
- **THEN** the `art` command is available and routes to `artifactr.cli:main`

#### Scenario: Module invocation
- **WHEN** `python -m artifactr` is run
- **THEN** the CLI is invoked identically to the `art` command

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
- **THEN** an `art create` subcommand is registered with a `skill` sub-subcommand

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

### Requirement: Default vault behavior
When no vault is explicitly specified, commands MUST use the default vault.

#### Scenario: Implicit default
- **WHEN** a command accepts a vault identifier and none is provided
- **THEN** the default vault from config is used

### Requirement: Vault identifier resolution
Any command that accepts a vault identifier MUST resolve it through a defined priority order.

#### Scenario: Resolution order
- **WHEN** a vault identifier is provided
- **THEN** it is resolved in order:
  1. Exact resolved filesystem path
  2. Vault name (from `vault_names`)
  3. Directory basename match

#### Scenario: Unique vault names
- **WHEN** a vault name is assigned
- **THEN** it MUST be unique across the catalog; assigning a name already in use by another vault MUST produce an error

### Requirement: Tool selection
Commands that operate on tools MUST support selecting specific tools or defaulting.

#### Scenario: Default tool
- **WHEN** no `--tools` flag is provided
- **THEN** the default tool is used

#### Scenario: Tool list
- **WHEN** `art tool list` is run
- **THEN** all supported tools are displayed with the current default indicated

#### Scenario: Tool select
- **WHEN** `art tool select <tool-name>` is run
- **THEN** the default tool is updated

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
