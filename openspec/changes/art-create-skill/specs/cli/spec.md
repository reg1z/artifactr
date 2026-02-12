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
