## MODIFIED Requirements

### Requirement: art tool add command
The `art tool add <name>` command MUST create a custom tool definition and store it in either the user global config or a vault's metadata file.

#### Scenario: Add tool to global config
- **WHEN** `art tool add my-tool --skills .my-tool/skills` is run (no `--vault` flag)
- **THEN** the tool definition MUST be saved to the user global config under `tools:`

#### Scenario: Add tool to global config with explicit flag
- **WHEN** `art tool add my-tool --skills .my-tool/skills -g` is run
- **THEN** the behavior MUST be identical to omitting `-g` (saved to global config)

#### Scenario: Add tool to vault
- **WHEN** `art tool add my-tool --skills .my-tool/skills --vault=team-vault` is run
- **THEN** the tool definition MUST be saved to the vault's `vault.yaml` under `tools:`

#### Scenario: Add tool with all paths
- **WHEN** `art tool add my-tool --skills .t/skills --commands .t/commands --agents .t/agents --global-skills '$HOME/.t/skills' --global-commands '$HOME/.t/commands' --global-agents '$HOME/.t/agents'` is run
- **THEN** all six path keys MUST be stored in the tool definition

#### Scenario: Add tool with alias
- **WHEN** `art tool add my-tool --skills .t/skills --alias mt` is run
- **THEN** the tool definition MUST include `aliases: ["mt"]`

#### Scenario: Add tool with multiple aliases via repeatable flag
- **WHEN** `art tool add my-tool --skills .t/skills --alias mt --alias mytool` is run
- **THEN** the tool definition MUST include `aliases: ["mt", "mytool"]`

#### Scenario: Add tool with multiple aliases via comma separation
- **WHEN** `art tool add my-tool --skills .t/skills --alias mt,mytool` is run
- **THEN** the tool definition MUST include `aliases: ["mt", "mytool"]`

#### Scenario: Add tool with mixed alias styles
- **WHEN** `art tool add my-tool --skills .t/skills --alias mt,mytool --alias m` is run
- **THEN** the tool definition MUST include `aliases: ["mt", "mytool", "m"]`

#### Scenario: Duplicate tool name
- **WHEN** `art tool add my-tool` is run and `my-tool` already exists in the target config
- **THEN** an error MUST be displayed and the command MUST exit with code 1

#### Scenario: Tool name conflicts with built-in
- **WHEN** `art tool add claude-code --skills .x/skills` is run targeting global config
- **THEN** it MUST succeed, creating a global config override of the built-in
