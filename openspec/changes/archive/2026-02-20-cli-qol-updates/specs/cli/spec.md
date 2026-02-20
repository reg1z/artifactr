## ADDED Requirements

### Requirement: Top-level -V shorthand for --version
The top-level `art` parser MUST accept `-V` as a short alias for `--version`.

#### Scenario: -V prints version
- **WHEN** `art -V` is run
- **THEN** the version string MUST be printed to stdout
- **AND** the output MUST be identical to `art --version`

#### Scenario: --version still accepted
- **WHEN** `art --version` is run
- **THEN** it MUST continue to work without any behavior change

### Requirement: Main help epilog labels artifact commands as "Artifact Operations"
The main `art --help` epilog section listing `ls`, `rm`, `copy`, `store`, `edit`, `cat`, `inspect`, `export`, and `create` MUST be headed "Artifact Operations", not "Vault Operations".

#### Scenario: Artifact Operations header in help output
- **WHEN** `art --help` is run
- **THEN** the help output MUST contain the heading "Artifact Operations:"
- **AND** MUST NOT contain the heading "Vault Operations:"
