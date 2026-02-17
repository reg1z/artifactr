## ADDED Requirements

### Requirement: Multi-vault resolution helper
A `_resolve_vault_paths()` helper MUST resolve repeatable, comma-separated `-V` flags into a list of vault filesystem paths.

#### Scenario: Single vault by name
- **WHEN** `-V favorites` is provided
- **THEN** the helper MUST return a list containing the resolved path for `favorites`

#### Scenario: Comma-separated vaults
- **WHEN** `-V vault1,vault2` is provided
- **THEN** the helper MUST return paths for both `vault1` and `vault2`

#### Scenario: Repeatable flag
- **WHEN** `-V vault1 -V vault2` is provided
- **THEN** the helper MUST return paths for both `vault1` and `vault2`

#### Scenario: Mixed repeatable and comma-separated
- **WHEN** `-V vault1,vault2 -V vault3` is provided
- **THEN** the helper MUST return paths for all three vaults

#### Scenario: No vault flag provided
- **WHEN** no `-V` flag is provided
- **THEN** the helper MUST return a list containing the default vault path

#### Scenario: Invalid vault name
- **WHEN** `-V nonexistent` is provided and the vault is not in the catalog
- **THEN** the helper MUST print an error and return an empty list

### Requirement: Multi-vault argparse pattern
Commands supporting multi-vault MUST use `action="append"` with help text indicating comma-separated and repeatable support.

#### Scenario: Argument definition
- **WHEN** a command supports multi-vault `-V`
- **THEN** the argparse argument MUST use `action="append"`, `dest="vaults"`, and help text: "Scope to vault(s) — comma-separated or repeatable (default: default vault)"

#### Scenario: Single-vault commands unchanged
- **WHEN** `art rm` or `art edit` defines `-V`
- **THEN** the argparse argument MUST NOT use `action="append"` and MUST remain single-value
