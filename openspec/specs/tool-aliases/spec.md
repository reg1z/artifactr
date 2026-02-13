## MODIFIED Requirements

### Requirement: Tool alias map
A mapping of tool aliases to canonical names MUST be derived from tool definitions (built-in, global config, and vault config) rather than maintained as a separate hardcoded dictionary.

#### Scenario: Claude alias
- **WHEN** aliases are resolved from tool definitions
- **THEN** `claude` MUST map to `claude-code` (defined in the `claude-code` built-in's `aliases` field)

#### Scenario: Extensibility
- **WHEN** a new alias needs to be added
- **THEN** it MUST only require adding an entry to the tool definition's `aliases` list (in built-in defaults, global config, or vault config)

### Requirement: Tool name resolution
A `resolve_tool_name()` function MUST resolve aliases to canonical names by scanning all loaded tool definitions for matching aliases.

#### Scenario: Known alias
- **WHEN** `resolve_tool_name("claude")` is called
- **THEN** it MUST return `"claude-code"`

#### Scenario: Canonical name passthrough
- **WHEN** `resolve_tool_name("claude-code")` is called
- **THEN** it MUST return `"claude-code"` unchanged

#### Scenario: Unknown name passthrough
- **WHEN** `resolve_tool_name("unknown-tool")` is called
- **THEN** it MUST return `"unknown-tool"` unchanged (validation happens elsewhere)

#### Scenario: Custom tool alias
- **WHEN** a user defines a tool with `aliases: ["cx"]` and `resolve_tool_name("cx")` is called
- **THEN** it MUST return the canonical tool name

### Requirement: Alias-aware tool lookup
The `get_tool()` function MUST resolve aliases before looking up the tool adapter.

#### Scenario: Lookup by alias
- **WHEN** `get_tool("claude")` is called
- **THEN** it MUST return the `GenericToolAdapter` instance for `claude-code`

#### Scenario: Lookup by canonical name
- **WHEN** `get_tool("claude-code")` is called
- **THEN** it MUST return the `GenericToolAdapter` instance for `claude-code`

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
The `art tool list` command MUST show aliases in a dedicated column.

#### Scenario: Alias display format
- **WHEN** `art tool list` is run and a tool has aliases
- **THEN** aliases MUST be displayed in a dedicated `Aliases` column

#### Scenario: No alias
- **WHEN** a tool has no aliases
- **THEN** the Aliases column MUST show `-` or be empty

## REMOVED Requirements

### Requirement: TOOL_ALIASES dict
**Reason**: Aliases are now stored within tool definitions rather than a separate `TOOL_ALIASES` dictionary.
**Migration**: Aliases are defined in the `aliases` field of each tool definition (built-in defaults, global config, or vault config).
