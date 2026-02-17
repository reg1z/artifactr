## ADDED Requirements

### Requirement: Tool list all flag
`art tool ls` MUST support `-a`/`--all` to list custom tool definitions from all catalog vaults.

#### Scenario: List all tools
- **WHEN** `art tool ls --all` is run
- **THEN** custom tool definitions from all catalog vaults and global config MUST be displayed

#### Scenario: All flag with vault column
- **WHEN** `art tool ls --all` is run
- **THEN** the output MUST include a SOURCE column indicating which vault or config each tool comes from

#### Scenario: All flag mutually exclusive with vault
- **WHEN** `art tool ls --all -V favorites` is run
- **THEN** an error MUST be displayed indicating `--all` and `--vault` cannot be used together

### Requirement: Tool info all flag
`art tool info` MUST support `-a`/`--all` to show all tool definitions from all sources.

#### Scenario: Info all without tool name
- **WHEN** `art tool info --all` is run without a tool name
- **THEN** all tool definitions from built-in, global config, and every catalog vault MUST be displayed

#### Scenario: Info all with tool name
- **WHEN** `art tool info --all <name>` is run
- **THEN** all definitions for that tool across all sources MUST be displayed

#### Scenario: All flag mutually exclusive with vault
- **WHEN** `art tool info --all -V favorites` is run
- **THEN** an error MUST be displayed indicating `--all` and `--vault` cannot be used together
