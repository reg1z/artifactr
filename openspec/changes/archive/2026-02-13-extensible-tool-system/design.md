## Context

Artifactr currently uses a hardcoded tool adapter pattern: each supported AI coding tool has a Python class (`ClaudeCodeAdapter`, `OpenCodeAdapter`) registered in `TOOL_REGISTRY`. Adding a new tool requires writing a new Python class and modifying registry code. All tools implicitly support all three artifact types (skills, commands, agents). There is no user-facing way to add custom tools, and no mechanism to express partial artifact support (e.g., Codex only supports skills).

Vaults are bare directories with no metadata file — vault names are stored externally in the global config.

## Goals / Non-Goals

**Goals:**
- Replace per-tool Python adapter classes with a single config-driven `GenericToolAdapter`
- Express built-in tools as data (Python dict) in the same schema as user-defined tools
- Allow users to define custom tools via CLI or YAML config, with per-artifact-type path configuration
- Support partial artifact coverage (tools that only handle a subset of artifact types)
- Introduce `vault.yaml` for portable vault metadata (name + tool definitions)
- Ship OpenAI Codex as a built-in default
- Add `art tool add`, `art tool rm`, `art tool show` CLI commands

**Non-Goals:**
- Supporting tool-specific artifact file formats (all tools use SKILL.md / .md conventions)
- Plugin system with hooks or custom tool behavior beyond path mapping
- Migrating existing user configs automatically (backwards-compatible, no migration needed)
- GUI/TUI for tool management

## Decisions

### 1. Single adapter class, tools as data

**Decision**: Replace `ClaudeCodeAdapter`, `OpenCodeAdapter`, and the `ToolAdapter` ABC with a single `GenericToolAdapter` class. All tools — built-in and custom — are defined as data dictionaries with the same schema.

**Rationale**: The existing adapter classes contain zero custom logic — they're pure path mappers. A data-driven approach eliminates the need to write Python code for new tools. If a tool ever needs custom behavior, we can cross that bridge later with adapter subclasses.

**Alternatives considered**:
- Keep ABC + per-tool classes, add `GenericToolAdapter` for custom tools only → Two systems to maintain, inconsistent
- Config-only (no Python dict for built-ins) → Requires config file to exist before first use, complicates packaging

### 2. Tool definition schema

**Decision**: Each tool is defined by a name and up to six optional path keys:

```yaml
tool-name:
  aliases: [alias1, alias2]
  skills: <repo-relative-path>        # e.g., .agents/skills
  commands: <repo-relative-path>       # e.g., .claude/commands
  agents: <repo-relative-path>         # e.g., .claude/agents
  global_skills: <absolute-path>       # e.g., $HOME/.agents/skills
  global_commands: <absolute-path>     # e.g., $HOME/.claude/commands
  global_agents: <absolute-path>       # e.g., $HOME/.claude/agents
```

Omitted path keys mean the tool does not support that artifact type. At least one of `skills`, `commands`, or `agents` must be present.

**Rationale**: Per-artifact-type paths accommodate tools like Codex where skills live in `.agents/skills` rather than `.codex/skills`. The implicit "omission = unsupported" contract is cleaner than an explicit `supported_types` list.

### 3. Three-tier tool resolution with precedence

**Decision**: Tools are resolved from three sources with ascending precedence:

1. **Built-in defaults** (Python dict `BUILTIN_TOOLS` in `tools/__init__.py`) — lowest precedence
2. **User global config** (`~/.config/artifactr/config.yaml` → `tools:` section)
3. **Vault config** (`<vault>/vault.yaml` → `tools:` section) — highest precedence

Higher precedence fully replaces a tool definition from a lower tier (no deep merging).

**Rationale**: Built-ins provide sensible defaults. Global config lets users customize for their setup. Vault config lets teams share tool definitions with their artifacts. Full replacement (not merge) keeps behavior predictable.

**Vault tool scope**: Vault tool definitions only participate in resolution when that vault is the active source (e.g., the vault being imported from). They don't globally affect the registry.

### 4. `vault.yaml` metadata file

**Decision**: Introduce an optional `vault.yaml` at vault root:

```yaml
name: my-vault
tools:
  custom-tool:
    skills: .custom/skills
```

The `name` field provides a portable vault name. The `tools` section defines vault-scoped tool definitions.

**Rationale**: Vault names currently live externally in the global config, meaning they don't travel when a vault is shared. Putting the name in the vault makes it portable. Adding tools here follows the same "metadata travels with the vault" principle.

**Backwards compatibility**: Vaults without `vault.yaml` continue working exactly as today. The file is entirely optional.

### 5. `GenericToolAdapter` interface

**Decision**: `GenericToolAdapter` stores the resolved tool config and exposes:

- `name` → tool identifier
- `supported_types` → list of artifact types this tool supports (derived from which path keys are present)
- `get_destination(artifact_type, target_repo)` → repo-local destination path
- `get_global_destination(artifact_type)` → global config destination path
- Both destination methods raise `ValueError` if the artifact type is unsupported

`$HOME` and `~` in path values are expanded at resolution time.

### 6. Alias system migration

**Decision**: Aliases move from the standalone `TOOL_ALIASES` dict into the tool definition's `aliases` field. The `resolve_tool_name()` function scans all tool definitions (built-in + config + vault) for matching aliases. `TOOL_ALIASES` dict is removed.

**Rationale**: Keeps alias information co-located with tool definitions. Users can add aliases to custom tools.

### 7. CLI commands for tool management

**Decision**:

- `art tool add <name> [--skills PATH] [--commands PATH] [--agents PATH] [--global-skills PATH] [--global-commands PATH] [--global-agents PATH] [--alias ALIAS]... [--vault VAULT | -g/--global]`
  - Default destination (no flag): user global config
  - `--vault=<name>`: writes to vault's `vault.yaml`
  - `-g`/`--global`: explicit alias for default behavior (writes to global config)

- `art tool rm <name> [--vault VAULT | -g/--global]`
  - Cannot remove built-in tools (error with message)
  - Removes from global config or vault config

- `art tool show <name>`
  - Displays resolved tool config: name, source, aliases, supported types with paths

- `art tool list` (enhanced)
  - Table with columns: Name, Source, Skills, Commands, Agents, Aliases
  - Source values: `built-in`, `user global config`, `vault:<name>`

## Risks / Trade-offs

- **[No deep merge across tiers]** → A vault override of a built-in tool must redefine all paths, even unchanged ones. Mitigation: document this clearly; most overrides will be for custom tools, not built-ins.
- **[vault.yaml name vs config.yaml vault_names]** → Two places to define a vault name. Mitigation: `vault.yaml` name is authoritative when present; `config.yaml` vault_names is fallback/override. Document precedence.
- **[$HOME expansion]** → Path values with `$HOME` or `~` need expansion. Mitigation: expand at resolution time in `GenericToolAdapter.__init__`, using `os.path.expandvars` and `Path.expanduser`.
- **[Removing ToolAdapter ABC]** → External code importing `ToolAdapter`, `ClaudeCodeAdapter`, or `OpenCodeAdapter` will break. Mitigation: this is an internal tool, not a library. No known external consumers.
