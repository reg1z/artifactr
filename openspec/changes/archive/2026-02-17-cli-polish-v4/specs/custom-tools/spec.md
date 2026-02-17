## MODIFIED Requirements

### Requirement: Tool add command
`art tool add` MUST support multi-vault `-V` to add a custom tool definition to multiple vaults.

#### Scenario: Add to single vault
- **WHEN** `art tool add <criteria> -V favorites` is run
- **THEN** the tool definition MUST be added to `favorites` vault.yaml

#### Scenario: Add to multiple vaults
- **WHEN** `art tool add <criteria> -V vault1,vault2` is run
- **THEN** the tool definition MUST be added to the vault.yaml of both `vault1` and `vault2`

#### Scenario: Add without vault flag
- **WHEN** `art tool add <criteria>` is run without `-V`
- **THEN** the tool definition MUST be added to the global config (existing behavior)

### Requirement: Tool list command
`art tool ls` MUST support multi-vault `-V` and an `--all` flag.

#### Scenario: List from single vault
- **WHEN** `art tool ls -V favorites` is run
- **THEN** tools from `favorites` MUST be listed

#### Scenario: List from multiple vaults
- **WHEN** `art tool ls -V vault1,vault2` is run
- **THEN** tools from both vaults MUST be listed

#### Scenario: List all catalog vaults
- **WHEN** `art tool ls --all` or `art tool ls -a` is run
- **THEN** tools from all catalog vaults and global config MUST be listed

#### Scenario: All flag mutually exclusive with vault
- **WHEN** `art tool ls --all -V favorites` is run
- **THEN** an error MUST be displayed

#### Scenario: List without flags
- **WHEN** `art tool ls` is run without `-V` or `--all`
- **THEN** tools from the default vault MUST be listed (existing behavior)

### Requirement: Tool info command
`art tool info` MUST support multi-vault `-V` and an `--all` flag.

#### Scenario: Info from single vault
- **WHEN** `art tool info -V favorites` is run
- **THEN** tool info from `favorites` MUST be shown

#### Scenario: Info from multiple vaults
- **WHEN** `art tool info -V vault1,vault2` is run
- **THEN** tool info from both vaults MUST be shown

#### Scenario: Info all sources
- **WHEN** `art tool info --all` or `art tool info -a` is run
- **THEN** tool definitions from built-in, global config, and every catalog vault MUST be shown

#### Scenario: All flag mutually exclusive with vault
- **WHEN** `art tool info --all -V favorites` is run
- **THEN** an error MUST be displayed

#### Scenario: Info without flags
- **WHEN** `art tool info` is run without `-V` or `--all`
- **THEN** tool info from the default vault MUST be shown (existing behavior)
