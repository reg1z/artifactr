## ADDED Requirements

### Requirement: Config namespace registration
The CLI MUST register a `config` subcommand with alias `conf` using argparse's `aliases` parameter. Both `art config <subcommand>` and `art conf <subcommand>` MUST be accepted.

#### Scenario: Using full name
- **WHEN** `art config import` is run
- **THEN** it MUST be handled identically to `art conf import`

#### Scenario: Using alias
- **WHEN** `art conf import` is run
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
`art conf list` MUST display globally imported artifacts by reading `.art-cache-global/imported`.

#### Scenario: List all
- **WHEN** `art conf list` is run
- **THEN** all globally imported artifacts MUST be listed

#### Scenario: List with type filter
- **WHEN** `art conf list -S` is run
- **THEN** only globally imported skills MUST be shown

#### Scenario: List with tool filter
- **WHEN** `art conf list --tools opencode` is run
- **THEN** only artifacts imported for opencode MUST be shown

#### Scenario: List with no imports
- **WHEN** `art conf list` is run and no `.art-cache-global` exists
- **THEN** a message MUST be displayed indicating no imported artifacts were found
