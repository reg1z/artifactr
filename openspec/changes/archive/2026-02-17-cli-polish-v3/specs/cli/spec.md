## ADDED Requirements

### Requirement: Vault shorthand flag
All commands that accept `--vault` MUST also accept `-V` as a shorthand.

#### Scenario: -V on ls
- **WHEN** `art ls -V my-vault` is run
- **THEN** it MUST behave identically to `art ls --vault my-vault`

#### Scenario: -V on rm
- **WHEN** `art rm artifact-name -V my-vault` is run
- **THEN** it MUST behave identically to `art rm artifact-name --vault my-vault`

#### Scenario: -V on store
- **WHEN** `art store ./dir -V my-vault` is run
- **THEN** it MUST behave identically to `art store ./dir --vault my-vault`

#### Scenario: -V on edit
- **WHEN** `art edit skill my-skill -V my-vault` is run
- **THEN** it MUST behave identically to `art edit skill my-skill --vault my-vault`

#### Scenario: -V on create
- **WHEN** `art create skill my-skill -d "desc" -V my-vault` is run
- **THEN** it MUST behave identically to `art create skill my-skill -d "desc" --vault my-vault`

#### Scenario: -V on project import
- **WHEN** `art proj import ./repo -V my-vault` is run
- **THEN** it MUST behave identically to `art proj import ./repo --vault my-vault`

#### Scenario: -V on config import
- **WHEN** `art conf import -V my-vault` is run
- **THEN** it MUST behave identically to `art conf import --vault my-vault`

#### Scenario: -V on tool add
- **WHEN** `art tool add my-tool -V my-vault` is run
- **THEN** it MUST behave identically to `art tool add my-tool --vault my-vault`

### Requirement: Store target_dir optional
The `store` command's `target_dir` positional argument MUST be optional (to support `--global` without a target).

#### Scenario: Store with target_dir
- **WHEN** `art store ./my-dir` is run
- **THEN** the positional argument MUST be accepted as before

#### Scenario: Store without target_dir
- **WHEN** `art store --global` is run without a positional argument
- **THEN** the command MUST proceed using global config directories as the source

### Requirement: Vault init yes flag
The `art vault init` command MUST accept `--yes`/`-y` for auto-confirmation of prompts.

#### Scenario: Vault init parser accepts yes
- **WHEN** `art vault init /path --yes` is parsed
- **THEN** argparse MUST accept the flag without error

### Requirement: Project import yes flag
The `art proj import` command MUST accept `--yes`/`-y` for auto-confirmation of prompts.

#### Scenario: Project import parser accepts yes
- **WHEN** `art proj import ./target --yes` is parsed
- **THEN** argparse MUST accept the flag without error

### Requirement: Spelunk depth flag
The `art spelunk` command MUST accept `--depth`/`-d` to control recursive scanning depth.

#### Scenario: Spelunk depth parser
- **WHEN** `art spelunk ./dir --depth 3` is parsed
- **THEN** argparse MUST accept the flag with an integer value

#### Scenario: Spelunk depth short flag
- **WHEN** `art spelunk ./dir -d 3` is parsed
- **THEN** it MUST behave identically to `--depth 3`

#### Scenario: Spelunk depth default
- **WHEN** `art spelunk ./dir` is run without `--depth`
- **THEN** the default depth MUST be 2

### Requirement: Spelunk format flag
The `art spelunk` command MUST accept `--format` to control output format.

#### Scenario: Spelunk format parser
- **WHEN** `art spelunk --format json` is parsed
- **THEN** argparse MUST accept the flag

#### Scenario: Valid format values
- **WHEN** `--format` is provided
- **THEN** the accepted values MUST be `human`, `json`, `yaml`, `md`, and `markdown`

#### Scenario: Format default
- **WHEN** `art spelunk` is run without `--format`
- **THEN** the default format MUST be `human`

### Requirement: Store tools flag
The `art store` command MUST accept `--tools` for filtering which tools' artifacts to store.

#### Scenario: Store tools parser
- **WHEN** `art store ./dir --tools claude-code` is parsed
- **THEN** argparse MUST accept the flag
