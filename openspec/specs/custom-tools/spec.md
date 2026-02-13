## ADDED Requirements

### Requirement: Tool definition schema
A tool definition MUST be a dictionary with the tool name as key and the following optional fields: `aliases` (list of strings), `skills` (repo-relative path), `commands` (repo-relative path), `agents` (repo-relative path), `global_skills` (absolute path), `global_commands` (absolute path), `global_agents` (absolute path). At least one of `skills`, `commands`, or `agents` MUST be present.

#### Scenario: Full tool definition
- **WHEN** a tool is defined with all path keys
- **THEN** the tool supports all three artifact types and has both repo-local and global paths for each

#### Scenario: Partial tool definition
- **WHEN** a tool is defined with only `skills` and `global_skills`
- **THEN** the tool supports only skills; commands and agents are unsupported

#### Scenario: Minimum valid definition
- **WHEN** a tool definition includes at least one of `skills`, `commands`, or `agents`
- **THEN** it MUST be considered valid

#### Scenario: Invalid definition
- **WHEN** a tool definition includes none of `skills`, `commands`, or `agents`
- **THEN** it MUST be rejected with an error

### Requirement: Built-in tool defaults
A `BUILTIN_TOOLS` dictionary MUST be maintained in the codebase containing default tool definitions for `claude-code`, `opencode`, and `codex`.

#### Scenario: Claude Code built-in
- **WHEN** the built-in tools are loaded
- **THEN** `claude-code` MUST be defined with aliases `["claude"]`, skills at `.claude/skills`, commands at `.claude/commands`, agents at `.claude/agents`, and corresponding global paths at `$HOME/.claude/skills`, `$HOME/.claude/commands`, `$HOME/.claude/agents`

#### Scenario: OpenCode built-in
- **WHEN** the built-in tools are loaded
- **THEN** `opencode` MUST be defined with skills at `.opencode/skills`, commands at `.opencode/commands`, agents at `.opencode/agents`, and corresponding global paths at `$HOME/.config/opencode/skills`, `$HOME/.config/opencode/commands`, `$HOME/.config/opencode/agents`

#### Scenario: Codex built-in
- **WHEN** the built-in tools are loaded
- **THEN** `codex` MUST be defined with only skills at `.agents/skills` and global skills at `$HOME/.agents/skills` (no commands or agents)

### Requirement: Three-tier tool resolution
Tools MUST be resolved from three sources with ascending precedence: built-in defaults (lowest), user global config, vault config (highest). A tool definition at a higher tier fully replaces the same-named tool from a lower tier.

#### Scenario: Built-in only
- **WHEN** a tool exists only in built-in defaults
- **THEN** the built-in definition is used

#### Scenario: Global config override
- **WHEN** a tool is defined in both built-in defaults and user global config
- **THEN** the user global config definition MUST fully replace the built-in definition

#### Scenario: Vault config override
- **WHEN** a tool is defined in both user global config and vault config
- **THEN** the vault config definition MUST fully replace the global config definition

#### Scenario: Vault tools scoped to active vault
- **WHEN** tools are resolved for an import operation
- **THEN** only tool definitions from the vault being imported from participate in resolution, not all registered vaults

### Requirement: User global config tool storage
Custom tool definitions MUST be storable in the user's global config file (`~/.config/artifactr/config.yaml`) under a `tools:` key.

#### Scenario: Tools section in config
- **WHEN** the global config is loaded and contains a `tools:` section
- **THEN** each entry MUST be parsed as a tool definition and added to the registry

#### Scenario: Missing tools section
- **WHEN** the global config has no `tools:` section
- **THEN** no user-defined global tools are loaded (built-in defaults still apply)

### Requirement: Path expansion
Path values containing `$HOME`, `~`, or other environment variables MUST be expanded at resolution time.

#### Scenario: $HOME expansion
- **WHEN** a tool definition contains `global_skills: $HOME/.agents/skills`
- **THEN** `$HOME` MUST be expanded to the user's home directory

#### Scenario: Tilde expansion
- **WHEN** a tool definition contains `global_skills: ~/.agents/skills`
- **THEN** `~` MUST be expanded to the user's home directory

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

#### Scenario: Add tool with multiple aliases
- **WHEN** `art tool add my-tool --skills .t/skills --alias mt --alias mytool` is run
- **THEN** the tool definition MUST include `aliases: ["mt", "mytool"]`

#### Scenario: Duplicate tool name
- **WHEN** `art tool add my-tool` is run and `my-tool` already exists in the target config
- **THEN** an error MUST be displayed and the command MUST exit with code 1

#### Scenario: Tool name conflicts with built-in
- **WHEN** `art tool add claude-code --skills .x/skills` is run targeting global config
- **THEN** it MUST succeed, creating a global config override of the built-in

### Requirement: art tool rm command
The `art tool rm <name>` command MUST remove a custom tool definition.

#### Scenario: Remove from global config
- **WHEN** `art tool rm my-tool` is run (no `--vault` flag)
- **THEN** the tool MUST be removed from the user global config's `tools:` section

#### Scenario: Remove from vault
- **WHEN** `art tool rm my-tool --vault=team-vault` is run
- **THEN** the tool MUST be removed from the vault's `vault.yaml` `tools:` section

#### Scenario: Remove built-in tool
- **WHEN** `art tool rm claude-code` is run and `claude-code` is only defined as a built-in
- **THEN** an error MUST be displayed: cannot remove built-in tool definitions

#### Scenario: Remove nonexistent tool
- **WHEN** `art tool rm nonexistent` is run
- **THEN** an error MUST be displayed and the command MUST exit with code 1

### Requirement: art tool show command
The `art tool show <name>` command MUST display the resolved configuration of a tool.

#### Scenario: Show built-in tool
- **WHEN** `art tool show claude-code` is run
- **THEN** output MUST include: tool name, source as `built-in`, aliases, and supported artifact types with their repo-local and global paths

#### Scenario: Show global config tool
- **WHEN** `art tool show my-tool` is run and `my-tool` is defined in global config
- **THEN** the source MUST be displayed as `user global config`

#### Scenario: Show vault tool
- **WHEN** `art tool show my-tool` is run and `my-tool` is defined in a vault
- **THEN** the source MUST be displayed as `vault (<vault-name>)`

#### Scenario: Show partial support
- **WHEN** `art tool show codex` is run
- **THEN** skills MUST show paths; commands and agents MUST show `(not supported)`

#### Scenario: Unknown tool
- **WHEN** `art tool show nonexistent` is run
- **THEN** an error MUST be displayed and the command MUST exit with code 1
