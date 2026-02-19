## ADDED Requirements

### Requirement: art cat prints artifact primary file content
The `art cat` command MUST print the raw content of an artifact's primary file to stdout.

#### Scenario: Cat a command artifact
- **WHEN** `art cat my-command` is run
- **THEN** the full content of `<vault>/commands/my-command.md` MUST be printed to stdout

#### Scenario: Cat an agent artifact
- **WHEN** `art cat my-agent` is run
- **THEN** the full content of `<vault>/agents/my-agent.md` MUST be printed to stdout

#### Scenario: Cat a skill artifact
- **WHEN** `art cat my-skill` is run and `my-skill` is a skill
- **THEN** the full content of `<vault>/skills/my-skill/SKILL.md` MUST be printed to stdout

#### Scenario: Cat with type prefix
- **WHEN** `art cat skill/my-skill` or `art cat sk/my-skill` is run
- **THEN** the primary file content of the named skill MUST be printed to stdout

#### Scenario: Cat resolves from default vault
- **WHEN** `art cat my-artifact` is run with no `-V` flag
- **THEN** the artifact MUST be resolved from the default vault

#### Scenario: Cat with explicit vault
- **WHEN** `art cat my-skill -V work` is run
- **THEN** the artifact MUST be resolved from the `work` vault

#### Scenario: Cat with --here resolves from project
- **WHEN** `art cat my-skill --here` is run
- **THEN** the artifact MUST be resolved from the current project's tool config directories

#### Scenario: Artifact not found
- **WHEN** `art cat nonexistent-artifact` is run
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

### Requirement: art cat accepts a sub-path for directory-based artifacts
`art cat` MUST accept a slash-delimited sub-path after the artifact name to print a specific file within a directory-based artifact.

#### Scenario: Cat specific file within skill
- **WHEN** `art cat my-skill/references/hooks.md` is run
- **THEN** the content of `<skill-dir>/references/hooks.md` MUST be printed to stdout

#### Scenario: Cat sub-path with type prefix
- **WHEN** `art cat sk/my-skill/references/hooks.md` is run
- **THEN** the content of `<skill-dir>/references/hooks.md` MUST be printed to stdout

#### Scenario: Cat sub-path file not found
- **WHEN** `art cat my-skill/nonexistent.md` is run and that path does not exist within the skill
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

#### Scenario: Sub-path on file-based artifact errors
- **WHEN** `art cat my-command/some-file.md` is run and `my-command` is a command
- **THEN** an error MUST be printed to stderr stating sub-paths are not supported for file-based artifacts

### Requirement: art cat supports frontmatter name fallback resolution
Artifact name resolution for `art cat` MUST follow the standard resolution order: exact filename/dirname match first, then frontmatter `name:` field fallback.

#### Scenario: Frontmatter name fallback
- **WHEN** `art cat display-name` is run and no artifact directory or file named `display-name` exists
- **BUT** a skill with `name: display-name` in its `SKILL.md` frontmatter exists
- **THEN** that skill's `SKILL.md` content MUST be printed
