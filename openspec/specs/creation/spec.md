## MODIFIED Requirements

### Requirement: Vault and project-local creation for commands and agents
Commands and agents MUST support the same `--vault`, `--here`, and `--tools` flags as skill creation. When using `--here` with `--tools`, the tool MUST support the artifact type being created.

#### Scenario: Vault target for command
- **WHEN** `art create command my-cmd -d "desc" --vault=favorites` is run
- **THEN** the command MUST be created at `<favorites-vault>/commands/my-cmd.md`

#### Scenario: Project-local command
- **WHEN** `art create command my-cmd -d "desc" --here` is run and the default tool is `claude-code`
- **THEN** the command MUST be created at `.claude/commands/my-cmd.md`

#### Scenario: Project-local agent with tools
- **WHEN** `art create agent my-agent -d "desc" --here --tools=claude-code,opencode` is run
- **THEN** the agent MUST be created in both `.claude/agents/my-agent.md` and `.opencode/agents/my-agent.md`

#### Scenario: Project-local with unsupported tool
- **WHEN** `art create command my-cmd -d "desc" --here --tools=codex` is run
- **THEN** an error MUST be displayed indicating codex does not support commands, and the command MUST exit with code 1

#### Scenario: Project-local skill with custom tool
- **WHEN** `art create skill my-skill -d "desc" --here --tools=codex` is run
- **THEN** the skill MUST be created at `.agents/skills/my-skill/` (using codex's configured skills path)
