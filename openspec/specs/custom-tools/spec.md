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

#### Scenario: Default vault tools in CLI resolution
- **WHEN** `art tool list` or `art tool select` is run
- **THEN** tool resolution MUST include the default vault's tool definitions as the vault tier

#### Scenario: Explicit vault override in CLI resolution
- **WHEN** `art tool list --vault=X` is run
- **THEN** vault X's tool definitions MUST replace the default vault's definitions in resolution

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

### Requirement: Active vault tool loading helper
A `load_active_vault_tools()` function MUST be provided that loads tool definitions from the default vault. It MUST return a tuple of `(tools_dict, vault_name)` where `tools_dict` is the tools from the default vault's `vault.yaml` and `vault_name` is the vault's display name. If no default vault is set, it MUST return `({}, None)`.

#### Scenario: Default vault with tools
- **WHEN** a default vault is set and its `vault.yaml` contains tool definitions
- **THEN** `load_active_vault_tools()` MUST return those tool definitions and the vault's name

#### Scenario: Default vault without tools
- **WHEN** a default vault is set but its `vault.yaml` has no `tools:` section
- **THEN** `load_active_vault_tools()` MUST return `({}, <vault_name>)`

#### Scenario: No default vault
- **WHEN** no default vault is set
- **THEN** `load_active_vault_tools()` MUST return `({}, None)`

### Requirement: All-vault tool catalog helper
A `load_all_vault_tools()` function MUST be provided that iterates all registered vaults and collects their tool definitions. It MUST return a list of tuples `(vault_name, vault_path, tools_dict)` for each registered vault.

#### Scenario: Multiple vaults with tools
- **WHEN** three vaults are registered and two have tool definitions
- **THEN** `load_all_vault_tools()` MUST return entries for all three vaults, with empty `tools_dict` for the vault without tools

#### Scenario: No registered vaults
- **WHEN** no vaults are registered
- **THEN** `load_all_vault_tools()` MUST return an empty list

### Requirement: art tool info command
The `art tool info` command MUST display tool definitions with support for catalog view (no name), detail view (with name), and source filtering (`--vault`, `--global`).

#### Scenario: Catalog view with no arguments
- **WHEN** `art tool info` is run with no arguments and no flags
- **THEN** output MUST display all tools grouped into sections: BUILT-IN, GLOBAL CONFIG (if any), one section per registered vault (if any), and CURRENT DIRECTORY (if `./vault.yaml` exists with tools). The default vault MUST be indicated with `(default)`.

#### Scenario: Detail view shows all definitions
- **WHEN** `art tool info <name>` is run with no filtering flags
- **THEN** output MUST display every definition of that tool across all tiers where it exists (built-in, global config, each vault, CWD). The definition that is currently active via three-tier resolution MUST be marked with `✓ ACTIVE`. Overridden definitions MUST be marked with `○` and `(overridden)`. Definitions in non-default vaults MUST be marked with `○` and `(not active)`. Each definition MUST show its aliases and supported artifact types with paths.

#### Scenario: Detail view with unknown tool name
- **WHEN** `art tool info nonexistent` is run
- **THEN** an error MUST be displayed and the command MUST exit with code 1

#### Scenario: Filter by specific vault
- **WHEN** `art tool info --vault=X` is run (with or without a tool name)
- **THEN** only tools from vault X MUST be displayed. Vault X MUST be resolvable by vault name or vault file path.

#### Scenario: Filter by default vault
- **WHEN** `art tool info --vault` is run with no value (with or without a tool name)
- **THEN** only tools from the currently selected default vault MUST be displayed

#### Scenario: Filter by default vault with no default set
- **WHEN** `art tool info --vault` is run with no value and no default vault is set
- **THEN** an error MUST be displayed indicating no default vault is configured

#### Scenario: Filter by global config
- **WHEN** `art tool info --global` is run (with or without a tool name)
- **THEN** only tools defined in the user's global config MUST be displayed

#### Scenario: Filter returns no results
- **WHEN** a filter flag is used and the specified source has no tool definitions (or no definition for the given name)
- **THEN** a message MUST be displayed indicating no tools were found in that source
