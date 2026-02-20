## ADDED Requirements

### Requirement: Shell wrapper passes help flags directly to art
When the shell wrapper function intercepts an `art nav` invocation, it MUST detect `--help` or `-h` among the nav arguments and route the entire command directly through `command art` without engaging the `--print` capture path.

#### Scenario: art nav --help shows formatted help
- **WHEN** `art nav --help` is run in a shell with the wrapper installed
- **THEN** the properly formatted help text for `art nav` MUST be printed to stdout
- **AND** the command MUST exit cleanly without a `cd` error

#### Scenario: art nav -h shows formatted help
- **WHEN** `art nav -h` is run in a shell with the wrapper installed
- **THEN** it MUST behave identically to `art nav --help`

#### Scenario: Help flag does not attempt navigation
- **WHEN** `art nav --help` is run
- **THEN** no `cd` command MUST be attempted
- **AND** the shell's current directory MUST remain unchanged

#### Scenario: Normal nav unaffected
- **WHEN** `art nav skills` is run without any help flags
- **THEN** the wrapper MUST continue to use the `--print` capture path to cd normally
