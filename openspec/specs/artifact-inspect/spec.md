## Purpose

Spec for the `art inspect` command, which displays parsed YAML frontmatter fields and (for directory-based artifacts) a file tree of all files within the artifact directory.

## Requirements

### Requirement: art inspect displays parsed frontmatter fields
The `art inspect` command MUST parse and display all YAML frontmatter key-value pairs from an artifact's primary file.

#### Scenario: Inspect command artifact
- **WHEN** `art inspect my-command` is run
- **THEN** all YAML frontmatter fields from `my-command.md` MUST be displayed as key-value pairs
- **AND** if the artifact has no frontmatter, a message MUST indicate that no frontmatter was found

#### Scenario: Inspect skill artifact
- **WHEN** `art inspect my-skill` is run
- **THEN** all YAML frontmatter fields from `SKILL.md` MUST be displayed as key-value pairs

#### Scenario: Inspect with type prefix
- **WHEN** `art inspect skill/my-skill` or `art inspect sk/my-skill` is run
- **THEN** frontmatter fields MUST be displayed for the named skill

#### Scenario: Inspect resolves from default vault
- **WHEN** `art inspect my-artifact` is run with no `-V` flag
- **THEN** the artifact MUST be resolved from the default vault

#### Scenario: Inspect with explicit vault
- **WHEN** `art inspect my-skill -V work` is run
- **THEN** the artifact MUST be resolved from the `work` vault

#### Scenario: Inspect with --here resolves from project
- **WHEN** `art inspect my-skill --here` is run
- **THEN** the artifact MUST be resolved from the current project's tool config directories

#### Scenario: Artifact not found
- **WHEN** `art inspect nonexistent` is run
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

### Requirement: art inspect displays file tree for directory-based artifacts
For directory-based artifacts (skills), `art inspect` MUST also display the file tree of all files within the artifact directory.

#### Scenario: File tree shown for skill
- **WHEN** `art inspect my-skill` is run and the skill contains additional files
- **THEN** a file tree MUST be displayed listing all files within the skill directory
- **AND** `SKILL.md` MUST be listed first and labeled as `(main)`
- **AND** files in subdirectories MUST be shown with their relative path

#### Scenario: No file tree for file-based artifacts
- **WHEN** `art inspect my-command` is run
- **THEN** no file tree section MUST be shown (commands and agents are single-file)

#### Scenario: Skill with only SKILL.md
- **WHEN** `art inspect my-skill` is run and the skill contains only `SKILL.md`
- **THEN** the file tree section MUST still show `SKILL.md` as the sole file

### Requirement: art inspect output format
The output of `art inspect` MUST follow a consistent, human-readable format.

#### Scenario: Output sections
- **WHEN** `art inspect` is run on a skill with frontmatter and multiple files
- **THEN** the output MUST include a "Frontmatter" section listing key: value pairs
- **AND** the output MUST include a "Files" section with the directory tree
- **AND** sections MUST be separated by a blank line

#### Scenario: Frontmatter output format
- **WHEN** frontmatter is displayed
- **THEN** each field MUST be shown as `  <key>: <value>` (2-space indent)
- **AND** multi-line or list values MUST be rendered in a readable form (not raw YAML flow style)

### Requirement: art inspect supports frontmatter name fallback resolution
Artifact name resolution for `art inspect` MUST follow the standard resolution order.

#### Scenario: Frontmatter name fallback
- **WHEN** `art inspect display-name` is run and no artifact named `display-name` exists by filename/dirname
- **BUT** an artifact with `name: display-name` in frontmatter exists
- **THEN** that artifact's inspection output MUST be shown
