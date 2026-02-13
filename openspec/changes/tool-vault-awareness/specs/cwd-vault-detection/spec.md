## ADDED Requirements

### Requirement: CWD vault.yaml detection
The system MUST be able to detect and parse a `vault.yaml` file in the current working directory to extract tool definitions.

#### Scenario: vault.yaml present in CWD
- **WHEN** a `vault.yaml` file exists in the current working directory
- **THEN** the system MUST read and parse its `tools:` section, returning the tool definitions

#### Scenario: vault.yaml absent from CWD
- **WHEN** no `vault.yaml` file exists in the current working directory
- **THEN** the system MUST return an empty tool definitions dict

#### Scenario: vault.yaml with no tools section
- **WHEN** a `vault.yaml` file exists in the current working directory but contains no `tools:` key
- **THEN** the system MUST return an empty tool definitions dict

### Requirement: CWD tools are informational only
Tool definitions detected from a CWD `vault.yaml` MUST NOT participate in tool resolution for `art tool list` or `art tool select`. They MUST only be displayed in the `art tool info` catalog view.

#### Scenario: CWD tools not in list resolution
- **WHEN** `art tool list` is run from a directory containing a `vault.yaml` with tool definitions
- **THEN** those CWD tools MUST NOT appear in the list output unless the directory is also the default vault

#### Scenario: CWD tools shown in info
- **WHEN** `art tool info` is run from a directory containing a `vault.yaml` with tool definitions
- **THEN** a "CURRENT DIRECTORY" section MUST be displayed showing those tools with source `current directory (./vault.yaml)`
