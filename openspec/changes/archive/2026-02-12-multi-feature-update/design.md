## Context

Artifactr is a CLI tool (`art`) for managing AI coding assistant artifacts (skills, agents, commands) across vaults and repositories. The codebase follows a pattern of decoupled logic: `catalog.py` for vault operations, `creator.py` for artifact creation, `importer.py` for import logic, `tools/__init__.py` for the tool registry, and `cli.py` for argument parsing and handler routing.

Currently, artifact creation only supports skills via a dedicated `create_skill()` function and hardcoded resolve functions. The tool registry maps canonical names to adapters with no alias support. Vault registration requires an existing directory and has no auto-naming.

## Goals / Non-Goals

**Goals:**
- Add vault initialization with directory scaffolding and automatic registration
- Auto-name vaults on add using `llm-vault-N` pattern
- Generalize artifact creation to support skills, commands, and agents
- Add artifact editing via terminal editor
- Add tool alias resolution (`claude` -> `claude-code`)
- Keep all changes additive and non-breaking

**Non-Goals:**
- TUI-based artifact creation (deferred to a future change)
- Interactive vault name prompting on collision (errors out instead)
- Editing project-local artifacts across all tools simultaneously (edits first match)
- Adding new tool adapters beyond claude-code and opencode

## Decisions

### 1. Auto-naming scheme: `llm-vault-N` with incrementing counter

Vault auto-naming scans all existing values in `config["vault_names"]` for names matching `llm-vault-\d+`, finds the highest N, and assigns `llm-vault-(N+1)`. If no `llm-vault-*` names exist, starts at `llm-vault-1`.

**Why not basename?** Basenames can collide across unrelated paths (e.g., two dirs named `vault/`). A predictable prefix with incrementing counter avoids collisions without user interaction.

**Alternative considered**: Prompt user for a name on collision. Rejected because the rest of the CLI is non-interactive for single-shot commands, and `art vault name` already exists for renaming.

### 2. Generalized `create_artifact()` function replacing `create_skill()`

A single `create_artifact(artifact_type, name, ...)` function handles all three types. The key branching point is storage format:

- **Skills**: Directory-based. Creates `<target>/SKILL.md` inside a new directory.
- **Commands/Agents**: File-based. Creates `<target>.md` as a flat file.

For commands, no `name` field is added to frontmatter (the filename IS the name). For agents, `name` is added to frontmatter (matching skill behavior).

The resolve functions (`resolve_vault_target`, `resolve_project_target`) are generalized to accept an `artifact_type` parameter. For directory-based types, the target is a directory path. For file-based types, the target is a file path (with `.md` extension).

**Why one function, not three?** The creation logic is 90% identical (frontmatter generation, overwrite protection, directory creation). The only differences are the file path and which frontmatter fields are included, which is handled by the `artifact_type` parameter.

### 3. Tool alias resolution at the registry level

A `TOOL_ALIASES` dict in `tools/__init__.py` maps aliases to canonical names. A `resolve_tool_name()` function is exposed for use by all consumers. `get_tool()` calls `resolve_tool_name()` internally.

All validation code that checks `if tool_name in supported_tools` is updated to resolve aliases first. `get_supported_tools()` continues to return only canonical names. Tool list display appends alias info.

**Why registry-level, not CLI-level?** Centralizing alias resolution ensures every code path (import, create, tool select) benefits from aliases without duplicating the mapping. The CLI doesn't need to know about aliases at all.

### 4. Editor resolution chain: `$VISUAL` -> `$EDITOR` -> `nano` -> `nvim `-> `vim` -> `vi`

A `get_editor()` utility function in `utils.py` checks environment variables first, then falls back to executables found via `shutil.which()`. The edit command runs `subprocess.run([editor, str(file_path)])` and returns the editor's exit code.

**Why `$VISUAL` first?** Convention from Unix systems: `$VISUAL` is for full-screen editors, `$EDITOR` is for line editors. Most modern users set `$EDITOR` but `$VISUAL` takes precedence when set.

### 5. `vault init` as idempotent add-or-create

`vault init <target_dir>` checks if the directory exists. If not, creates it with `skills/`, `agents/`, `commands/` subdirectories. If it does exist, skips scaffolding. Either way, calls `add_vaults()` for registration. This means running `vault init` twice is safe — the second run just registers (or skips if already registered).

The `--name` flag maps to the existing `add_vaults(name=...)` parameter. Without `--name`, auto-naming from Decision 1 applies.

### 6. `art edit` with `--here` support

In vault mode (default), resolves the artifact in the default or specified vault. In `--here` mode, resolves in the current project's tool config directory using the default tool or `--tools` flag. If `--tools` specifies multiple tools, edits the first match found.

The artifact path resolution follows the same pattern as vault hierarchy scanning in `catalog.py`: skills are directories containing `SKILL.md`, commands/agents are `.md` files.

## Risks / Trade-offs

- **Auto-naming may surprise users** who expect basename-based names -> Mitigated by printing informative output showing the assigned name and how to change it.
- **Generalized `create_artifact()` changes existing function signature** -> `create_skill()` is replaced, but all callers are internal (just `cli.py`). Tests will be updated.
- **Editor fallback chain may not find any editor** -> Function returns `None` and the CLI prints a clear error: "No editor found. Set $EDITOR or install nano, neovim, vim, or vi."
- **`--here` edit with multiple tools only edits first match** -> Acceptable for now; editing the same artifact in multiple tool dirs simultaneously would be confusing. Users can specify `--tools=<specific>` to target a particular one.
