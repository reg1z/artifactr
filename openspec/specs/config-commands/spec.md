## Requirements

### Requirement: Config namespace registration
The CLI MUST register a `config` subcommand with aliases `conf` and `c` using argparse's `aliases` parameter. `art config <subcommand>`, `art conf <subcommand>`, and `art c <subcommand>` MUST all be accepted.

#### Scenario: Using full name
- **WHEN** `art config import` is run
- **THEN** it MUST be handled identically to `art conf import`

#### Scenario: Using alias
- **WHEN** `art conf import` is run
- **THEN** it MUST invoke the config import handler

#### Scenario: Using single-letter alias
- **WHEN** `art c import` is run
- **THEN** it MUST invoke the config import handler

### Requirement: Config import command
`art conf import` MUST import artifacts from a vault into global config directories.

#### Scenario: Basic global import
- **WHEN** `art conf import` is run
- **THEN** artifacts from the default vault MUST be imported into global config directories for the default tool

#### Scenario: Import with vault selection
- **WHEN** `--vault=<name-or-path>` is provided
- **THEN** artifacts MUST be imported from that vault

#### Scenario: Import with tool filtering
- **WHEN** `--tools=<tool1,tool2>` is provided
- **THEN** only the specified tools' global directories MUST receive artifacts

#### Scenario: Import with artifact selection
- **WHEN** `--artifacts=<name1,name2>` is provided
- **THEN** only the named artifacts MUST be imported

#### Scenario: Import with link mode
- **WHEN** `-l`/`--link` is provided
- **THEN** artifacts MUST be symlinked instead of copied

#### Scenario: Import with force mode
- **WHEN** `-f`/`--force` is provided
- **THEN** existing files MUST be overwritten without prompting

#### Scenario: Import with type filters
- **WHEN** `-S`/`--skills`, `-C`/`--commands`, or `-A`/`--agents` flags are provided
- **THEN** only artifact types matching the flags MUST be imported

#### Scenario: Import with named type filters
- **WHEN** `-C foo,bar` is provided
- **THEN** only commands named `foo` and `bar` MUST be imported globally

#### Scenario: Missing global directory prompt
- **WHEN** a tool's global directory does not exist
- **THEN** the user MUST be prompted to create it

### Requirement: Config rm command
`art conf rm <names...>` MUST remove globally imported artifacts.

#### Scenario: Remove by name
- **WHEN** `art conf rm foo` is run
- **THEN** the globally imported artifact named `foo` MUST be located and deleted

#### Scenario: Remove with type filter
- **WHEN** `art conf rm foo -S` is run
- **THEN** only the globally imported skill named `foo` MUST be removed

#### Scenario: Remove with tool filter
- **WHEN** `art conf rm foo --tools claude-code` is run
- **THEN** only artifacts in claude-code's global directories MUST be searched

#### Scenario: Remove with confirmation
- **WHEN** `art conf rm foo` is run without `--force`
- **THEN** a confirmation prompt MUST be shown

#### Scenario: Remove with force
- **WHEN** `art conf rm foo -f` is run
- **THEN** artifacts MUST be removed without confirmation

#### Scenario: Remove updates global cache
- **WHEN** an artifact is successfully removed
- **THEN** its entry MUST be removed from `~/.config/artifactr/.art-cache-global/imported`

### Requirement: Config wipe command
`art conf wipe` MUST remove all globally imported artifacts.

#### Scenario: Wipe all
- **WHEN** `art conf wipe` is run
- **THEN** all artifacts tracked in `.art-cache-global/imported` MUST be deleted

#### Scenario: Wipe with confirmation
- **WHEN** `art conf wipe` is run without `--force`
- **THEN** a confirmation prompt MUST be shown listing what will be removed

#### Scenario: Wipe with force
- **WHEN** `art conf wipe -f` is run
- **THEN** artifacts MUST be removed without confirmation

#### Scenario: Wipe with type filter
- **WHEN** `art conf wipe -S` is run
- **THEN** only globally imported skill artifacts MUST be removed

#### Scenario: Wipe with tool filter
- **WHEN** `art conf wipe --tools opencode` is run
- **THEN** only artifacts imported for opencode MUST be removed

#### Scenario: Wipe clears global cache
- **WHEN** artifacts are successfully wiped
- **THEN** corresponding entries MUST be removed from `.art-cache-global/imported`

#### Scenario: Wipe with no cache
- **WHEN** `art conf wipe` is run and no `.art-cache-global` directory exists
- **THEN** a message MUST be displayed indicating no imported artifacts were found

### Requirement: Config list command
`art config ls` MUST display globally imported artifacts by reading `.art-cache-global/imported`.

#### Scenario: List all
- **WHEN** `art config ls` is run
- **THEN** all globally imported artifacts MUST be listed

#### Scenario: List with type filter
- **WHEN** `art config ls -S` is run
- **THEN** only globally imported skills MUST be shown

#### Scenario: List with tool filter
- **WHEN** `art config ls --tools opencode` is run
- **THEN** only artifacts imported for opencode MUST be shown

#### Scenario: List with no imports
- **WHEN** `art config ls` is run and no `.art-cache-global` exists
- **THEN** a message MUST be displayed indicating no imported artifacts were found

### Requirement: Config edit subcommand
The `config` namespace MUST expose an `edit` subcommand.

#### Scenario: Config edit registration
- **WHEN** `art config` help is displayed
- **THEN** `edit` MUST appear in the list of available subcommands

### Requirement: Config link command
`art conf link` MUST be registered as a subcommand of the `config` namespace with alias `ln`.

#### Scenario: Command registration
- **WHEN** `art conf --help` is displayed
- **THEN** `link` MUST appear in the list of available subcommands

#### Scenario: Alias registration
- **WHEN** `art conf ln` is run
- **THEN** it MUST invoke the config link handler

#### Scenario: Positional arguments
- **WHEN** `art conf link name1 name2` is run
- **THEN** `name1` and `name2` MUST be parsed as artifact names (nargs='*')

#### Scenario: All flag
- **WHEN** `art conf link --all` or `art conf link -a` is run
- **THEN** the `all` flag MUST be set to True

#### Scenario: Force flag
- **WHEN** `art conf link --force` or `art conf link -f` is run
- **THEN** the `force` flag MUST be set to True

#### Scenario: Vault flag — scoping
- **WHEN** `art conf link -V vault1,vault2` or `art conf link -V vault1 -V vault2` is run
- **THEN** the operation MUST be scoped to artifacts imported from the specified vaults

#### Scenario: No vault flag (default)
- **WHEN** `art conf link -a` is run without `--vault`
- **THEN** the operation MUST be scoped to the currently selected default vault

### Requirement: Config unlink command
`art conf unlink` MUST be registered as a subcommand of the `config` namespace with alias `uln`.

#### Scenario: Command registration
- **WHEN** `art conf --help` is displayed
- **THEN** `unlink` MUST appear in the list of available subcommands

#### Scenario: Alias registration
- **WHEN** `art conf uln` is run
- **THEN** it MUST invoke the config unlink handler

#### Scenario: Positional arguments
- **WHEN** `art conf unlink name1` is run
- **THEN** `name1` MUST be parsed as an artifact name

#### Scenario: All flag
- **WHEN** `art conf unlink --all` or `art conf unlink -a` is run
- **THEN** the `all` flag MUST be set to True

#### Scenario: Vault flag on unlink
- **WHEN** `art conf unlink -V favorites` is run
- **THEN** the operation MUST be scoped to artifacts imported from `favorites` only

#### Scenario: No vault flag on unlink (default)
- **WHEN** `art conf unlink -a` is run without `--vault`
- **THEN** the operation MUST be scoped to the currently selected default vault

### Requirement: Config list vault filter
`art conf ls` MUST support `-V`/`--vault` to filter listed artifacts by vault.

#### Scenario: List with single vault filter
- **WHEN** `art conf ls -V favorites` is run
- **THEN** only globally imported artifacts from `favorites` MUST be displayed

#### Scenario: List with multiple vault filter
- **WHEN** `art conf ls -V vault1,vault2` is run
- **THEN** only globally imported artifacts from `vault1` or `vault2` MUST be displayed

#### Scenario: List without vault filter
- **WHEN** `art conf ls` is run without `-V`
- **THEN** artifacts from all vaults MUST be displayed (existing behavior)

### Requirement: Config rm vault filter
`art conf rm` MUST support `-V`/`--vault` to scope removal by vault.

#### Scenario: Remove with vault filter
- **WHEN** `art conf rm foo -V favorites` is run
- **THEN** only the globally imported artifact named `foo` from `favorites` MUST be removed

#### Scenario: Remove with multiple vault filter
- **WHEN** `art conf rm foo -V vault1,vault2` is run
- **THEN** the artifact named `foo` from either `vault1` or `vault2` MUST be removed

### Requirement: Config wipe vault filter
`art conf wipe` MUST support `-V`/`--vault` to scope wipe by vault.

#### Scenario: Wipe with vault filter
- **WHEN** `art conf wipe -V favorites` is run
- **THEN** only globally imported artifacts from `favorites` MUST be removed

#### Scenario: Wipe with multiple vault filter
- **WHEN** `art conf wipe -V vault1,vault2` is run
- **THEN** only globally imported artifacts from `vault1` or `vault2` MUST be removed

#### Scenario: Wipe without vault filter
- **WHEN** `art conf wipe` is run without `-V`
- **THEN** all globally imported artifacts MUST be removed (existing behavior)
