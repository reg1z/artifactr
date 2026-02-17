## ADDED Requirements

### Requirement: Frontmatter name fallback resolution
When the artifact name provided to `art edit` does not match a folder or file name in the target vault, the system MUST fall back to searching YAML frontmatter `name` fields.

#### Scenario: Folder match takes priority
- **WHEN** `art edit skill greet` is run and `<vault>/skills/greet/SKILL.md` exists
- **THEN** that file MUST be opened regardless of any frontmatter `name` fields in other skills

#### Scenario: Frontmatter fallback for skills
- **WHEN** `art edit skill greet` is run and no folder `greet` exists under `<vault>/skills/`
- **BUT** a skill at `<vault>/skills/my-greeting/SKILL.md` has `name: greet` in its YAML frontmatter
- **THEN** `<vault>/skills/my-greeting/SKILL.md` MUST be opened

#### Scenario: Frontmatter fallback for agents
- **WHEN** `art edit agent helper` is run and no file `helper.md` exists under `<vault>/agents/`
- **BUT** `<vault>/agents/my-helper.md` has `name: helper` in its YAML frontmatter
- **THEN** `<vault>/agents/my-helper.md` MUST be opened

#### Scenario: Frontmatter fallback for commands
- **WHEN** `art edit command deploy` is run and no file `deploy.md` exists under `<vault>/commands/`
- **BUT** `<vault>/commands/my-deploy.md` has `name: deploy` in its YAML frontmatter
- **THEN** `<vault>/commands/my-deploy.md` MUST be opened

#### Scenario: Frontmatter parsing scope
- **WHEN** scanning for frontmatter `name` fields
- **THEN** the system MUST only parse content between the opening `---` and closing `---` YAML frontmatter delimiters, not the full file

#### Scenario: Multiple frontmatter matches
- **WHEN** multiple artifacts of the same type have the same `name` in frontmatter
- **THEN** the first match in alphabetical filesystem order MUST be used

#### Scenario: No match found
- **WHEN** neither a folder/file match nor a frontmatter `name` match is found
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

#### Scenario: Frontmatter fallback with --here
- **WHEN** `art edit skill greet --here` is run and no folder `greet` exists in the project
- **THEN** the frontmatter fallback MUST also apply to project-local artifacts
