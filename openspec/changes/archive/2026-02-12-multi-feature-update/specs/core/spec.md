## ADDED Requirements

### Requirement: Tool alias registry
The tool registry MUST maintain a mapping of aliases to canonical tool names.

#### Scenario: Alias map contents
- **WHEN** the alias map is loaded
- **THEN** it MUST contain at minimum: `{"claude": "claude-code"}`

#### Scenario: Resolve function
- **WHEN** `resolve_tool_name()` is called with an alias
- **THEN** it MUST return the canonical name

#### Scenario: Passthrough for canonical names
- **WHEN** `resolve_tool_name()` is called with a canonical name
- **THEN** it MUST return the name unchanged

#### Scenario: Passthrough for unknown names
- **WHEN** `resolve_tool_name()` is called with an unrecognized name
- **THEN** it MUST return the name unchanged

### Requirement: Alias-aware get_tool
The `get_tool()` function MUST resolve aliases internally.

#### Scenario: Get tool by alias
- **WHEN** `get_tool("claude")` is called
- **THEN** it MUST return the `ClaudeCodeAdapter` instance

#### Scenario: Get tool by canonical name
- **WHEN** `get_tool("claude-code")` is called
- **THEN** it MUST return the `ClaudeCodeAdapter` instance (unchanged behavior)

### Requirement: Reverse alias lookup
A function MUST exist to find aliases for a given canonical tool name.

#### Scenario: Get aliases for tool
- **WHEN** aliases are looked up for `claude-code`
- **THEN** the result MUST include `claude`

#### Scenario: No aliases for tool
- **WHEN** aliases are looked up for `opencode`
- **THEN** the result MUST be an empty list

## MODIFIED Requirements

### Requirement: Supported tools
Artifactr MUST support `claude-code` and `opencode` as import targets.

#### Scenario: Modular tool support
- **WHEN** a new tool needs to be supported
- **THEN** tool support MUST be implemented using a modular/extensible pattern (base class) where each tool adapter defines the tool's name/identifier and destination paths for each artifact type

#### Scenario: Tool adapter reads from vault
- **WHEN** a tool adapter performs an import
- **THEN** it reads from the same tool-agnostic vault structure and writes to tool-specific destinations

#### Scenario: Tool alias support
- **WHEN** a tool name is provided by the user in any context
- **THEN** it MUST be resolved through the alias map before being used for lookup or validation
