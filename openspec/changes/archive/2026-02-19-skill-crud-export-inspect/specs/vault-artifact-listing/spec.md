## ADDED Requirements

### Requirement: art ls accepts an artifact name to list files within a directory-based artifact
`art ls` MUST accept an optional positional artifact-name argument. When provided, it MUST list the files within that artifact's directory rather than listing vault artifacts.

#### Scenario: List files within a skill
- **WHEN** `art ls my-skill` is run and `my-skill` is a skill in the default vault
- **THEN** all files within the skill's directory MUST be listed
- **AND** `SKILL.md` MUST be listed first and labeled as `(main)`
- **AND** files in subdirectories MUST be shown with their relative path

#### Scenario: List files with type prefix
- **WHEN** `art ls skill/my-skill` or `art ls sk/my-skill` is run
- **THEN** files within the named skill MUST be listed

#### Scenario: List files with explicit vault
- **WHEN** `art ls my-skill -V work` is run
- **THEN** files within `my-skill` in the `work` vault MUST be listed

#### Scenario: File-based artifact errors
- **WHEN** `art ls my-command` is run and `my-command` is a command (file-based)
- **THEN** an error MUST be printed to stderr stating that `my-command` is a file-based artifact and does not support file listing
- **AND** the command MUST exit with code 1

#### Scenario: Artifact name not found
- **WHEN** `art ls nonexistent` is run and no artifact by that name is found in the default vault
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

#### Scenario: Skill with only SKILL.md
- **WHEN** `art ls my-skill` is run and the skill contains only `SKILL.md`
- **THEN** only `SKILL.md` MUST be listed (labeled as `(main)`)

#### Scenario: No artifact name — existing behavior preserved
- **WHEN** `art ls` is run with no positional argument
- **THEN** the existing vault artifact listing behavior MUST apply (list all artifacts in the default vault)
