## MODIFIED Requirements

### Requirement: Project import command
`art proj import [target]` MUST import artifacts from a vault into a target directory. The target does not need to be a git repository.

#### Scenario: Import with explicit target
- **WHEN** `art proj import /path/to/repo` is run
- **THEN** artifacts MUST be imported into `/path/to/repo`

#### Scenario: Import with cwd default
- **WHEN** `art proj import` is run without a target argument
- **THEN** the current working directory MUST be used as the target

#### Scenario: Import into non-git directory with prompt
- **WHEN** the resolved target is not a git repository
- **THEN** the user MUST be prompted: "Target is not a git repository. Continue without git integration? [Y/n]"
- **AND** if confirmed, the import MUST proceed and the `.git/info/exclude` step MUST be skipped entirely
- **AND** if declined, the command MUST abort

#### Scenario: Import into non-git directory with --yes
- **WHEN** the resolved target is not a git repository and `--yes` is provided
- **THEN** the import MUST proceed without prompting, skipping the `.git/info/exclude` step

#### Scenario: Import into git directory
- **WHEN** the resolved target is a git repository
- **THEN** the import MUST proceed normally including the `.git/info/exclude` step (existing behavior)

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
- **WHEN** `--no-exclude` is provided and the target is a git repository
- **THEN** imported artifact paths MUST NOT be added to `.git/info/exclude`
- **AND** `.art-cache` MUST still be added to `.git/info/exclude`
- **AND** import cache tracking in `.art-cache/imported` MUST still be performed

#### Scenario: Import without no-exclude flag
- **WHEN** `--no-exclude` is not provided and the target is a git repository
- **THEN** imported artifact paths MUST be added to `.git/info/exclude` (existing behavior)
