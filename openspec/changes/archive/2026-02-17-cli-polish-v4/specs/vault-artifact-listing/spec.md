## MODIFIED Requirements

### Requirement: List vault contents
`art ls` MUST display artifacts in a vault, with multi-vault support.

#### Scenario: List single vault (default)
- **WHEN** `art ls` is run without `-V`
- **THEN** artifacts from the default vault MUST be listed with columns NAME, TYPE, TOOL

#### Scenario: List single vault by name
- **WHEN** `art ls -V favorites` is run
- **THEN** artifacts from `favorites` MUST be listed with columns NAME, TYPE, TOOL

#### Scenario: List multiple vaults
- **WHEN** `art ls -V vault1,vault2` is run
- **THEN** artifacts from both vaults MUST be listed with columns NAME, TYPE, TOOL, VAULT

#### Scenario: Vault column added for multi-vault
- **WHEN** multiple vaults are specified via `-V`
- **THEN** a VAULT column MUST be added to the output indicating which vault each artifact belongs to

#### Scenario: Vault column absent for single vault
- **WHEN** a single vault is listed (default or single `-V`)
- **THEN** the VAULT column MUST NOT be shown

#### Scenario: Multi-vault with type filter
- **WHEN** `art ls -V vault1,vault2 -S` is run
- **THEN** only skills from both vaults MUST be listed
