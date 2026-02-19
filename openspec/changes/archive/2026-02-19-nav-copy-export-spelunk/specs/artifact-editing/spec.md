## MODIFIED Requirements

### Requirement: Frontmatter name fallback resolution
When an artifact name provided to any artifact name-matching command does not match a folder or file name in the target search scope, the system MUST fall back to searching YAML frontmatter `name` fields.

#### Scenario: Folder match takes priority
- **WHEN** an artifact name is resolved and `<vault>/skills/<name>/SKILL.md` exists
- **THEN** that artifact MUST be used regardless of any frontmatter `name` fields in other artifacts

#### Scenario: Frontmatter fallback for skills
- **WHEN** an artifact name is resolved, no folder `<name>` exists under `<vault>/skills/`
- **BUT** a skill at `<vault>/skills/my-skill/SKILL.md` has `name: <name>` in its YAML frontmatter
- **THEN** that skill MUST be matched

#### Scenario: Frontmatter fallback for agents
- **WHEN** an artifact name is resolved, no file `<name>.md` exists under `<vault>/agents/`
- **BUT** `<vault>/agents/my-helper.md` has `name: <name>` in its YAML frontmatter
- **THEN** that agent MUST be matched

#### Scenario: Frontmatter fallback for commands
- **WHEN** an artifact name is resolved, no file `<name>.md` exists under `<vault>/commands/`
- **BUT** `<vault>/commands/my-deploy.md` has `name: <name>` in its YAML frontmatter
- **THEN** that command MUST be matched

#### Scenario: Frontmatter parsing scope
- **WHEN** scanning for frontmatter `name` fields
- **THEN** the system MUST only parse content between the opening `---` and closing `---` YAML frontmatter delimiters, not the full file

#### Scenario: Multiple frontmatter matches
- **WHEN** multiple artifacts of the same type have the same `name` in frontmatter
- **THEN** the first match in alphabetical filesystem order MUST be used

#### Scenario: No match found
- **WHEN** neither a folder/file match nor a frontmatter `name` match is found
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

#### Scenario: Frontmatter fallback applies to art edit
- **WHEN** `art edit skill <name>` is run and no folder `<name>` exists in the target vault
- **THEN** the frontmatter fallback MUST apply (same as general rule above)

#### Scenario: Frontmatter fallback applies to art copy
- **WHEN** `art copy <name> <dest>` is run and no artifact named `<name>` exists by filename/dirname
- **THEN** the frontmatter fallback MUST apply

#### Scenario: Frontmatter fallback applies to art edit --here
- **WHEN** `art edit skill <name> --here` is run and no folder `<name>` exists in the project
- **THEN** the frontmatter fallback MUST also apply to project-local artifacts

#### Scenario: Convention applies to all future artifact name-matching commands
- **WHEN** any command resolves an artifact by name
- **THEN** the resolution order MUST be: (1) exact filename/dirname match, (2) frontmatter `name:` field fallback
