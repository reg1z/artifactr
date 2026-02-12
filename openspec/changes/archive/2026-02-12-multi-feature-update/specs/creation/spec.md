## ADDED Requirements

### Requirement: Command creation
The `art create command <name>` command MUST create a new command as a flat markdown file with YAML frontmatter.

#### Scenario: Basic command creation
- **WHEN** `art create command my-cmd -d "Run deployment"` is run
- **THEN** a file `my-cmd.md` MUST be created at `<default-vault>/commands/my-cmd.md` with frontmatter containing `description: Run deployment` and NO `name` field

#### Scenario: Command file format
- **WHEN** a command is created
- **THEN** the file MUST follow the format:
  ```
  ---
  description: <description>
  [additional fields]
  ---
  <content>
  ```

#### Scenario: Command name is filename
- **WHEN** `art create command deploy-prod` is run
- **THEN** the file MUST be named `deploy-prod.md` and no `name` field MUST appear in frontmatter

#### Scenario: Description required for commands
- **WHEN** `art create command my-cmd` is run without `--description`
- **THEN** an error MUST be printed with usage hint and the command MUST exit with code 1

#### Scenario: Command with content
- **WHEN** `art create command my-cmd -d "desc" -c "Instructions here"` is run
- **THEN** the markdown body "Instructions here" MUST appear after the frontmatter

#### Scenario: Command with extra fields
- **WHEN** `art create command my-cmd -d "desc" -D key=value` is run
- **THEN** the `key: value` field MUST appear in frontmatter

#### Scenario: Command overwrite protection
- **WHEN** `art create command my-cmd` is run and `my-cmd.md` already exists at the target
- **THEN** an error MUST be printed and the command MUST exit with code 1

### Requirement: Agent creation
The `art create agent <name>` command MUST create a new agent as a flat markdown file with YAML frontmatter.

#### Scenario: Basic agent creation
- **WHEN** `art create agent my-agent -d "Handles reviews"` is run
- **THEN** a file `my-agent.md` MUST be created at `<default-vault>/agents/my-agent.md` with frontmatter containing `name: my-agent` and `description: Handles reviews`

#### Scenario: Agent file format
- **WHEN** an agent is created
- **THEN** the file MUST follow the format:
  ```
  ---
  name: <name>
  description: <description>
  [additional fields]
  ---
  <content>
  ```

#### Scenario: Agent name in frontmatter
- **WHEN** `art create agent code-reviewer` is run
- **THEN** the frontmatter MUST contain `name: code-reviewer`

#### Scenario: Description required for agents
- **WHEN** `art create agent my-agent` is run without `--description`
- **THEN** an error MUST be printed with usage hint and the command MUST exit with code 1

#### Scenario: Agent with content and extra fields
- **WHEN** `art create agent my-agent -d "desc" -c "Body" -D model=sonnet` is run
- **THEN** the file MUST contain frontmatter with `name`, `description`, `model` fields and "Body" as the markdown content

#### Scenario: Agent overwrite protection
- **WHEN** `art create agent my-agent` is run and `my-agent.md` already exists at the target
- **THEN** an error MUST be printed and the command MUST exit with code 1

### Requirement: Vault and project-local creation for commands and agents
Commands and agents MUST support the same `--vault`, `--here`, and `--tools` flags as skill creation.

#### Scenario: Vault target for command
- **WHEN** `art create command my-cmd -d "desc" --vault=favorites` is run
- **THEN** the command MUST be created at `<favorites-vault>/commands/my-cmd.md`

#### Scenario: Project-local command
- **WHEN** `art create command my-cmd -d "desc" --here` is run and the default tool is `claude-code`
- **THEN** the command MUST be created at `.claude/commands/my-cmd.md`

#### Scenario: Project-local agent with tools
- **WHEN** `art create agent my-agent -d "desc" --here --tools=claude-code,opencode` is run
- **THEN** the agent MUST be created in both `.claude/agents/my-agent.md` and `.opencode/agents/my-agent.md`

## MODIFIED Requirements

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

### Requirement: Description required
The `art create` command MUST require `--description` / `-d` for all artifact types.

#### Scenario: Missing description for skill
- **WHEN** `art create skill my-skill` is run without `--description`
- **THEN** an error is printed with usage hint and the command exits with code 1

#### Scenario: Missing description for command
- **WHEN** `art create command my-cmd` is run without `--description`
- **THEN** an error is printed with usage hint and the command exits with code 1

#### Scenario: Missing description for agent
- **WHEN** `art create agent my-agent` is run without `--description`
- **THEN** an error is printed with usage hint and the command exits with code 1
