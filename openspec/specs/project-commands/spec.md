## ADDED Requirements

### Requirement: Project namespace registration
The CLI MUST register a `project` subcommand with alias `proj` using argparse's `aliases` parameter. Both `art project <subcommand>` and `art proj <subcommand>` MUST be accepted.

#### Scenario: Using full name
- **WHEN** `art project import` is run
- **THEN** it MUST be handled identically to `art proj import`

#### Scenario: Using alias
- **WHEN** `art proj import` is run
- **THEN** it MUST invoke the project import handler

### Requirement: Project import command
`art proj import [target]` MUST import artifacts from a vault into a project repository.

#### Scenario: Import with explicit target
- **WHEN** `art proj import /path/to/repo` is run
- **THEN** artifacts MUST be imported into `/path/to/repo`

#### Scenario: Import with cwd default
- **WHEN** `art proj import` is run without a target argument
- **THEN** the current working directory MUST be used as the target

#### Scenario: Import target validation
- **WHEN** the resolved target is not a git repository
- **THEN** an error MUST be displayed

#### Scenario: Import with vault selection
- **WHEN** `--vault=<name-or-path>` is provided
- **THEN** artifacts MUST be imported from that vault instead of the default

#### Scenario: Import with tool filtering
- **WHEN** `--tools=<tool1,tool2>` is provided
- **THEN** only the specified tools' artifacts MUST be imported

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
- **WHEN** `-S foo,bar` is provided
- **THEN** only skills named `foo` and `bar` MUST be imported

#### Scenario: Import with no-exclude flag
- **WHEN** `--no-exclude` is provided
- **THEN** imported artifact paths MUST NOT be added to `.git/info/exclude`
- **AND** `.art-cache` MUST still be added to `.git/info/exclude`
- **AND** import cache tracking in `.art-cache/imported` MUST still be performed

#### Scenario: Import without no-exclude flag
- **WHEN** `--no-exclude` is not provided
- **THEN** imported artifact paths MUST be added to `.git/info/exclude` (existing behavior)

### Requirement: Project rm command
`art proj rm <names...>` MUST remove imported artifacts from a project.

#### Scenario: Remove by name from cwd
- **WHEN** `art proj rm foo` is run without `--target`
- **THEN** the artifact named `foo` MUST be located and deleted from the current working directory

#### Scenario: Remove by qualified name
- **WHEN** `art proj rm skills/foo` is run
- **THEN** only the skill named `foo` MUST be removed (no ambiguity prompt)

#### Scenario: Remove with target flag
- **WHEN** `art proj rm foo --target /path/to/repo` is run
- **THEN** the artifact MUST be removed from the specified project path

#### Scenario: Remove with type filter
- **WHEN** `art proj rm foo -S` is run
- **THEN** only the skill artifact named `foo` MUST be removed

#### Scenario: Remove with tool filter
- **WHEN** `art proj rm foo --tools claude-code` is run
- **THEN** only artifacts in claude-code's directories MUST be searched for removal

#### Scenario: Remove with confirmation
- **WHEN** `art proj rm foo` is run without `--force`
- **THEN** a confirmation prompt MUST be shown listing what will be removed

#### Scenario: Remove with force
- **WHEN** `art proj rm foo -f` is run
- **THEN** artifacts MUST be removed without confirmation

#### Scenario: Remove updates import cache
- **WHEN** an artifact is successfully removed from a project
- **THEN** its entry MUST be removed from `.art-cache/imported`

#### Scenario: Ambiguous name without type filter
- **WHEN** `art proj rm foo` is run and `foo` exists as both a skill and a command
- **THEN** the user MUST be prompted to disambiguate

### Requirement: Project wipe command
`art proj wipe` MUST remove all imported artifacts from a project.

#### Scenario: Wipe from cwd
- **WHEN** `art proj wipe` is run without `--target`
- **THEN** all artifacts tracked in `.art-cache/imported` MUST be deleted from the current working directory

#### Scenario: Wipe with target
- **WHEN** `art proj wipe --target /path/to/repo` is run
- **THEN** all tracked artifacts MUST be deleted from the specified project

#### Scenario: Wipe with confirmation
- **WHEN** `art proj wipe` is run without `--force`
- **THEN** a confirmation prompt MUST be shown listing all artifacts that will be removed

#### Scenario: Wipe with force
- **WHEN** `art proj wipe -f` is run
- **THEN** artifacts MUST be removed without confirmation

#### Scenario: Wipe with type filter
- **WHEN** `art proj wipe -S` is run
- **THEN** only skill artifacts MUST be removed; commands and agents MUST be preserved

#### Scenario: Wipe with tool filter
- **WHEN** `art proj wipe --tools claude-code` is run
- **THEN** only artifacts imported for claude-code MUST be removed

#### Scenario: Wipe clears cache
- **WHEN** artifacts are successfully wiped
- **THEN** corresponding entries MUST be removed from `.art-cache/imported`

#### Scenario: Wipe with no cache
- **WHEN** `art proj wipe` is run and no `.art-cache` directory exists
- **THEN** a message MUST be displayed indicating no imported artifacts were found

### Requirement: Project list command
`art proj list` MUST display artifacts imported into a project by reading `.art-cache/imported`.

#### Scenario: List from cwd
- **WHEN** `art proj list` is run without `--target`
- **THEN** imported artifacts in the current working directory MUST be listed

#### Scenario: List with target
- **WHEN** `art proj list --target /path/to/repo` is run
- **THEN** imported artifacts in the specified project MUST be listed

#### Scenario: List with type filter
- **WHEN** `art proj list -S` is run
- **THEN** only imported skill artifacts MUST be shown

#### Scenario: List with tool filter
- **WHEN** `art proj list --tools claude-code` is run
- **THEN** only artifacts imported for claude-code MUST be shown

#### Scenario: List with no imports
- **WHEN** `art proj list` is run and no `.art-cache` exists
- **THEN** a message MUST be displayed indicating no imported artifacts were found
