## Requirements

### Requirement: Skill scaffolding
The `art create skill <name>` command MUST create a new skill with a `SKILL.md` file containing YAML frontmatter and optional markdown content.

#### Scenario: Minimal skill creation
- **WHEN** `art create skill my-skill --description="A helpful skill"` is run
- **THEN** a `SKILL.md` file is created with frontmatter containing at minimum `name: my-skill` and `description: A helpful skill`

#### Scenario: Full non-interactive creation
- **WHEN** `art create skill my-skill -d "A skill" -c "Instructions here" -D author=Jane -D version=1.0` is run
- **THEN** the `SKILL.md` file contains frontmatter with `name`, `description`, `author`, `version` fields and the markdown body "Instructions here"

#### Scenario: Name override
- **WHEN** `art create skill my-skill --name="My Display Name"` is run
- **THEN** the frontmatter `name` field is set to "My Display Name" and the directory is named `my-skill`

#### Scenario: SKILL.md format
- **WHEN** a skill is created with frontmatter fields and content
- **THEN** the file MUST follow the format:
  ```
  ---
  name: <name>
  description: <description>
  [additional fields]
  ---
  <content>
  ```

### Requirement: Vault creation (default)
By default, skills MUST be created in the default vault's skill directory.

#### Scenario: Default vault target
- **WHEN** `art create skill my-skill` is run without `--here`
- **THEN** the skill is created at `<default-vault>/skills/my-skill/SKILL.md`

#### Scenario: Explicit vault target
- **WHEN** `art create skill my-skill --vault=favorites` is run
- **THEN** the skill is created at `<favorites-vault>/skills/my-skill/SKILL.md`

#### Scenario: No default vault
- **WHEN** `art create skill my-skill` is run and no default vault is set
- **THEN** an error is printed to stderr and the command exits with code 1

#### Scenario: Invalid vault
- **WHEN** `--vault=nonexistent` is provided and the vault is not in the catalog
- **THEN** an error is printed to stderr and the command exits with code 1

### Requirement: Project-local creation
When `--here` / `-H` is provided, skills MUST be created in the current project's tool config directory.

#### Scenario: Default tool
- **WHEN** `art create skill my-skill --here` is run and the default tool is `claude-code`
- **THEN** the skill is created at `.claude/skills/my-skill/SKILL.md` relative to the current directory

#### Scenario: Explicit tools
- **WHEN** `art create skill my-skill --here --tools=claude-code,opencode` is run
- **THEN** the skill is created in both `.claude/skills/my-skill/SKILL.md` and `.opencode/skills/my-skill/SKILL.md`

#### Scenario: Tools flag without here
- **WHEN** `--tools` is provided without `--here`
- **THEN** `--tools` is ignored (vault creation is tool-agnostic)

### Requirement: Overwrite protection
The command MUST NOT silently overwrite an existing skill.

#### Scenario: Skill already exists
- **WHEN** `art create skill my-skill` is run and `my-skill` already exists at the target location
- **THEN** an error is printed: "Skill 'my-skill' already exists at <path>" and the command exits with code 1

### Requirement: Description required
The command MUST require `--description` / `-d` to create a skill.

#### Scenario: Missing description
- **WHEN** `art create skill my-skill` is run without `--description`
- **THEN** an error is printed with usage hint and the command exits with code 1

#### Scenario: Description provided
- **WHEN** `art create skill my-skill -d "A helpful skill"` is run
- **THEN** the skill is created with the provided description

#### Scenario: Positional name always required
- **WHEN** `art create skill` is run without a name argument
- **THEN** argparse displays a usage error

### Requirement: Non-interactive flag definitions
The command MUST support the following flags with both short and long forms.

#### Scenario: Name flag
- **WHEN** `-n <value>` or `--name=<value>` is provided
- **THEN** the frontmatter `name` field is set to `<value>`, overriding the positional argument

#### Scenario: Description flag
- **WHEN** `-d <value>` or `--description=<value>` is provided
- **THEN** the frontmatter `description` field is set to `<value>`

#### Scenario: Content flag
- **WHEN** `-c <value>` or `--content=<value>` is provided
- **THEN** the markdown body after frontmatter is set to `<value>`

#### Scenario: Field flag
- **WHEN** `-D key=value` or `--field key=value` is provided (repeatable)
- **THEN** each key-value pair is added to the frontmatter

#### Scenario: Multiple field flags
- **WHEN** `-D author=Jane -D version=1.0` is provided
- **THEN** both `author: Jane` and `version: "1.0"` appear in frontmatter

#### Scenario: Here flag
- **WHEN** `-H` or `--here` is provided
- **THEN** the skill is created in the current project instead of a vault

### Requirement: Known fields registry
A registry of known frontmatter fields MUST be maintained for use by help text and future TUI integration.

#### Scenario: Field entry structure
- **WHEN** a known field is registered
- **THEN** it MUST include: name, description, field type (text/boolean/select), supported tools list, and optionally default value and select options

#### Scenario: Claude Code fields
- **WHEN** the registry is loaded
- **THEN** it MUST include at minimum: `argument-hint`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `model`, `context`, `agent` with descriptions and correct field types

#### Scenario: Extensibility
- **WHEN** a new tool's fields need to be added
- **THEN** entries can be added to the registry without modifying other code
