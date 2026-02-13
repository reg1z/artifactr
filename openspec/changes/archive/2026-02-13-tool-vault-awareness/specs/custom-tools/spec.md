## ADDED Requirements

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

## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: art tool show command
**Reason**: Replaced by `art tool info` command which provides both single-tool detail view and comprehensive catalog view.
**Migration**: Use `art tool info <name>` for the same single-tool detail behavior, or `art tool info` with no arguments for the new catalog view.
