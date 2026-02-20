## ADDED Requirements

### Requirement: Spelunk defaults to current working directory
When `art spelunk` is invoked without a positional target argument, it MUST spelunk the current working directory rather than global config directories.

#### Scenario: No target — spelunks CWD
- **WHEN** `art spelunk` is run with no positional argument and without `-g`/`--global`
- **THEN** the system MUST discover artifacts in the current working directory
- **AND** the LOCATION column MUST display paths relative to the current working directory

#### Scenario: Explicit target overrides CWD default
- **WHEN** `art spelunk ./some-dir` is run with an explicit target
- **THEN** the system MUST spelunk `./some-dir` as before (no behavior change)

#### Scenario: -g flag targets global config
- **WHEN** `art spelunk -g` is run (equivalently: `--global`)
- **THEN** the system MUST spelunk global config directories (the previous no-argument behavior)
- **AND** LOCATION column MUST display home-collapsed absolute paths (`~/...`)

#### Scenario: -g with explicit target is accepted
- **WHEN** `art spelunk ./some-dir -g` is run
- **THEN** the `-g` flag takes precedence and global config directories MUST be spelunked

#### Scenario: No "no target" notice for CWD default
- **WHEN** `art spelunk` is run with no positional argument
- **THEN** the system MUST NOT print a "No target specified" notice
