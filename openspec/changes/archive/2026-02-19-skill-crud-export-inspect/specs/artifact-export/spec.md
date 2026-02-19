## ADDED Requirements

### Requirement: art export packages a single artifact as a zip archive
The `art export` command MUST export a single artifact to a `.zip` file preserving the artifact's directory structure.

#### Scenario: Export a skill artifact
- **WHEN** `art export my-skill` is run
- **THEN** a zip file named `my-skill.zip` MUST be created in the current working directory
- **AND** the zip MUST contain `my-skill/SKILL.md` at its root
- **AND** any additional files within the skill directory MUST be included under `my-skill/`

#### Scenario: Export a command artifact
- **WHEN** `art export my-command` is run
- **THEN** a zip file named `my-command.zip` MUST be created in the current working directory
- **AND** the zip MUST contain `my-command/my-command.md` (wrapped in a named directory)

#### Scenario: Export an agent artifact
- **WHEN** `art export my-agent` is run
- **THEN** a zip file named `my-agent.zip` MUST be created in the current working directory
- **AND** the zip MUST contain `my-agent/my-agent.md`

#### Scenario: Export with type prefix
- **WHEN** `art export skill/my-skill` or `art export sk/my-skill` is run
- **THEN** the named skill MUST be exported as a zip

#### Scenario: Export resolves from default vault
- **WHEN** `art export my-artifact` is run with no `-V` flag
- **THEN** the artifact MUST be resolved from the default vault

#### Scenario: Export with explicit vault
- **WHEN** `art export my-skill -V work` is run
- **THEN** the artifact MUST be resolved from the `work` vault

#### Scenario: Artifact not found
- **WHEN** `art export nonexistent` is run
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

### Requirement: art export accepts a custom output path
The `art export` command MUST accept an optional `-o` / `--output` argument to specify the zip file destination.

#### Scenario: Custom output path
- **WHEN** `art export my-skill -o ~/Desktop/my-skill.zip` is run
- **THEN** the zip MUST be written to `~/Desktop/my-skill.zip` (with `~` expansion)

#### Scenario: Output path directory does not exist
- **WHEN** `-o /nonexistent/dir/out.zip` is specified and the parent directory does not exist
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

#### Scenario: Output path already exists
- **WHEN** the output path already exists as a file
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

### Requirement: art export zip archive internal structure
The zip archive produced by `art export` MUST follow a consistent internal structure.

#### Scenario: Skill archive structure
- **WHEN** a skill is exported
- **THEN** all files within the skill directory MUST be placed under a top-level directory named after the artifact (its folder name, not frontmatter name)
- **AND** relative paths of subdirectory files MUST be preserved

#### Scenario: Command/agent archive structure
- **WHEN** a command or agent is exported
- **THEN** the `.md` file MUST be placed at `<artifact-name>/<artifact-name>.md` within the zip
- **AND** no additional files MUST be added

#### Scenario: No manifest file in exported artifact zip
- **WHEN** any artifact is exported
- **THEN** the zip MUST NOT contain a `manifest.yaml` or any metadata file beyond the artifact's own files

### Requirement: art export supports frontmatter name fallback resolution
Artifact name resolution for `art export` MUST follow the standard resolution order.

#### Scenario: Frontmatter name fallback
- **WHEN** `art export display-name` is run and no artifact named `display-name` exists by filename/dirname
- **BUT** an artifact with `name: display-name` in frontmatter exists
- **THEN** that artifact MUST be exported
