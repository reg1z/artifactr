## ADDED Requirements

### Requirement: Supported types derivation
A tool's supported artifact types MUST be derived from which path keys are present in its definition. If `skills` is defined, skills are supported. If `commands` is defined, commands are supported. If `agents` is defined, agents are supported.

#### Scenario: Full support
- **WHEN** a tool definition includes `skills`, `commands`, and `agents` keys
- **THEN** `supported_types` MUST be `["skills", "commands", "agents"]`

#### Scenario: Skills only
- **WHEN** a tool definition includes only `skills` (like codex)
- **THEN** `supported_types` MUST be `["skills"]`

#### Scenario: Skills and commands only
- **WHEN** a tool definition includes `skills` and `commands` but not `agents`
- **THEN** `supported_types` MUST be `["skills", "commands"]`

### Requirement: Destination for unsupported types
When `get_destination()` or `get_global_destination()` is called with an unsupported artifact type, the adapter MUST raise a `ValueError`.

#### Scenario: Unsupported type destination
- **WHEN** `get_destination("commands", target_repo)` is called on a tool that only supports skills
- **THEN** a `ValueError` MUST be raised

#### Scenario: Supported type destination
- **WHEN** `get_destination("skills", target_repo)` is called on a tool that supports skills
- **THEN** the resolved path MUST be returned

### Requirement: Import skips unsupported types
During import, artifact types not supported by the target tool MUST be silently skipped.

#### Scenario: Import to partial tool
- **WHEN** `art import <target> --tools=codex` is run and the vault contains skills, commands, and agents
- **THEN** only skills MUST be imported; commands and agents MUST be skipped without error

#### Scenario: Import to full tool
- **WHEN** `art import <target> --tools=claude-code` is run
- **THEN** all artifact types MUST be imported as before

### Requirement: Creation validates tool support
When creating an artifact with `--here` and `--tools`, the tool MUST support the artifact type being created.

#### Scenario: Create unsupported type
- **WHEN** `art create command my-cmd -d "desc" --here --tools=codex` is run
- **THEN** an error MUST be displayed indicating codex does not support commands

#### Scenario: Create supported type
- **WHEN** `art create skill my-skill -d "desc" --here --tools=codex` is run
- **THEN** the skill MUST be created at `.agents/skills/my-skill/`

### Requirement: Discovery respects tool support
When discovering artifacts for a specific tool, only supported artifact types MUST be scanned.

#### Scenario: Spelunk with partial tool
- **WHEN** artifacts are discovered for a tool that only supports skills
- **THEN** only `skills/` directories MUST be scanned; `commands/` and `agents/` MUST be skipped

#### Scenario: Store with partial tool
- **WHEN** `art store` discovers artifacts from a tool that only supports skills
- **THEN** only skill artifacts from that tool's config directory MUST be listed for selection
