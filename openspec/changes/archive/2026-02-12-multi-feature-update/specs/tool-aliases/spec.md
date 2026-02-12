## ADDED Requirements

### Requirement: Tool alias map
A mapping of tool aliases to canonical names MUST be maintained in the tool registry.

#### Scenario: Claude alias
- **WHEN** the alias map is loaded
- **THEN** `claude` MUST map to `claude-code`

#### Scenario: Extensibility
- **WHEN** a new alias needs to be added
- **THEN** it MUST only require adding an entry to the `TOOL_ALIASES` dict

### Requirement: Tool name resolution
A `resolve_tool_name()` function MUST resolve aliases to canonical names.

#### Scenario: Known alias
- **WHEN** `resolve_tool_name("claude")` is called
- **THEN** it MUST return `"claude-code"`

#### Scenario: Canonical name passthrough
- **WHEN** `resolve_tool_name("claude-code")` is called
- **THEN** it MUST return `"claude-code"` unchanged

#### Scenario: Unknown name passthrough
- **WHEN** `resolve_tool_name("unknown-tool")` is called
- **THEN** it MUST return `"unknown-tool"` unchanged (validation happens elsewhere)

### Requirement: Alias-aware tool lookup
The `get_tool()` function MUST resolve aliases before looking up the tool adapter.

#### Scenario: Lookup by alias
- **WHEN** `get_tool("claude")` is called
- **THEN** it MUST return the `ClaudeCodeAdapter` instance

#### Scenario: Lookup by canonical name
- **WHEN** `get_tool("claude-code")` is called
- **THEN** it MUST continue to return the `ClaudeCodeAdapter` instance

### Requirement: Alias-aware validation
All code paths that validate tool names against the supported tools list MUST resolve aliases first.

#### Scenario: Import with alias
- **WHEN** `art import <target> --tools=claude` is run
- **THEN** the alias MUST be resolved to `claude-code` before validation and the import MUST succeed

#### Scenario: Create with alias
- **WHEN** `art create skill my-skill --here --tools=claude` is run
- **THEN** the alias MUST be resolved to `claude-code` and the skill MUST be created in `.claude/skills/my-skill/`

#### Scenario: Tool select with alias
- **WHEN** `art tool select claude` is run
- **THEN** the default tool MUST be set to `claude-code`

### Requirement: Tool list alias display
The `art tool list` command MUST show aliases alongside canonical names.

#### Scenario: Alias display format
- **WHEN** `art tool list` is run and a tool has aliases
- **THEN** the alias MUST be displayed in parentheses: `claude-code (alias: claude)`

#### Scenario: No alias
- **WHEN** a tool has no aliases
- **THEN** only the canonical name is displayed (no alias annotation)
