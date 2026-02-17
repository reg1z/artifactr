## Requirements

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

### Requirement: Project link command
`art proj link` MUST be registered as a subcommand of the `project` namespace with alias `ln`.

#### Scenario: Command registration
- **WHEN** `art proj --help` is displayed
- **THEN** `link` MUST appear in the list of available subcommands

#### Scenario: Alias registration
- **WHEN** `art proj ln` is run
- **THEN** it MUST invoke the project link handler

#### Scenario: Positional arguments
- **WHEN** `art proj link name1 name2` is run
- **THEN** `name1` and `name2` MUST be parsed as artifact names (nargs='*')

#### Scenario: All flag
- **WHEN** `art proj link --all` or `art proj link -a` is run
- **THEN** the `all` flag MUST be set to True

#### Scenario: Force flag
- **WHEN** `art proj link --force` or `art proj link -f` is run
- **THEN** the `force` flag MUST be set to True

#### Scenario: Vault flag — single vault
- **WHEN** `art proj link --vault favorites` or `art proj link -V favorites` is run
- **THEN** the operation MUST be scoped to artifacts imported from `favorites` only

#### Scenario: Vault flag — multiple vaults (comma-separated)
- **WHEN** `art proj link -V vault1,vault2` is run
- **THEN** the operation MUST be scoped to artifacts imported from both `vault1` and `vault2`

#### Scenario: Vault flag — multiple vaults (repeatable)
- **WHEN** `art proj link -V vault1 -V vault2` is run
- **THEN** it MUST behave identically to `-V vault1,vault2`

#### Scenario: No vault flag (default)
- **WHEN** `art proj link -a` is run without `--vault`
- **THEN** the operation MUST be scoped to the currently selected default vault

#### Scenario: Type filter flags
- **WHEN** `art proj link -S` is run
- **THEN** only skill artifacts MUST be targeted

### Requirement: Project unlink command
`art proj unlink` MUST be registered as a subcommand of the `project` namespace with alias `uln`.

#### Scenario: Command registration
- **WHEN** `art proj --help` is displayed
- **THEN** `unlink` MUST appear in the list of available subcommands

#### Scenario: Alias registration
- **WHEN** `art proj uln` is run
- **THEN** it MUST invoke the project unlink handler

#### Scenario: Positional arguments
- **WHEN** `art proj unlink name1` is run
- **THEN** `name1` MUST be parsed as an artifact name

#### Scenario: All flag
- **WHEN** `art proj unlink --all` or `art proj unlink -a` is run
- **THEN** the `all` flag MUST be set to True

#### Scenario: Vault flag on unlink
- **WHEN** `art proj unlink -V favorites` is run
- **THEN** the operation MUST be scoped to artifacts imported from `favorites` only

#### Scenario: No vault flag on unlink (default)
- **WHEN** `art proj unlink -a` is run without `--vault`
- **THEN** the operation MUST be scoped to the currently selected default vault
