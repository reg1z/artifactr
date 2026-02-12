## Context

Artifactr currently supports discovering, storing, and importing artifacts but has no creation flow. Users must manually create directories and write YAML frontmatter. The codebase follows a pattern of decoupled business logic (catalog.py, importer.py, scanner.py) with CLI handlers in cli.py and tool-specific behavior in tools/. The only external dependency is PyYAML.

This change adds `art create skill <name>` with flag-based creation requiring `--description`. The TUI for interactive creation is implemented on a separate `TUI` branch, decoupled from the CLI. `textual` is added as a dependency for future TUI integration.

## Goals / Non-Goals

**Goals:**
- Scaffold skills in vaults or project-local tool directories with correct structure
- Support flag-based creation with `--description` required
- Keep the known-fields registry extensible as new tools are added
- Maintain the tool-agnostic philosophy

**Non-Goals:**
- Creating agents or commands (future work — only skills for now)
- Editing existing skills
- TUI integration into CLI (deferred to `TUI` branch)
- Validating tool-specific field values

## Decisions

### 1. Module structure

**Decision:** Two new modules on main in `src/artifactr/`:
- `creator.py` — Business logic for skill scaffolding (frontmatter generation, file writing, path resolution)
- `known_fields.py` — Registry of known frontmatter fields with metadata (description, type, supported tools, input widget hint)

A third module, `tui.py`, is implemented on the `TUI` branch and not wired into the CLI on main.

**Rationale:** Follows the existing pattern of decoupled logic. `creator.py` handles the "what" (building the SKILL.md content and writing it), `known_fields.py` is a pure data module that both the future TUI and help/docs features can reference. The CLI handler in cli.py orchestrates flag-based creation directly.

**Alternative considered:** Putting known fields inside the TUI module. Rejected because the field registry is useful beyond the TUI (e.g., `--help` text, future validation, documentation generation).

### 2. Non-interactive flag design (Option C hybrid)

**Decision:** First-class flags for common fields (`-n/--name`, `-d/--description`, `-c/--content`), plus `-D/--field key=value` (repeatable) for arbitrary frontmatter.

**Rationale:** `description` is always needed and deserves proper help text. Arbitrary fields via `-D` avoid polluting the argparse namespace with every possible frontmatter key while keeping the syntax clean. The `-D` convention is well-established from Java/Maven/CMake for arbitrary key-value pairs.

**Alternative considered:** `parse_known_args()` to allow any `--key value` flag. Rejected due to ambiguity (system flags vs frontmatter fields) and complexity.

### 3. Description required

**Decision:** `--description` / `-d` is required. Without it, the command prints a usage error. There is no auto-TUI launch — all creation is flag-based on main.

**Rationale:** The TUI was decoupled to a separate branch during implementation. Requiring description ensures skills always have meaningful metadata. The flag-based interface is sufficient for scripting and direct usage.

**Previous decision (deferred):** Mode detection that auto-launched the TUI when no content flags were provided. This is implemented on the `TUI` branch.

### 4. Textual TUI structure (deferred to `TUI` branch)

**Decision:** A single Textual `App` with a form layout. Implemented on the `TUI` branch, not wired into the CLI on main. See `TUI` branch for details.

### 5. Known fields registry structure

**Decision:** A list of dataclass/dict entries, each with:
- `name`: field key (e.g., `"disable-model-invocation"`)
- `description`: brief explanation
- `field_type`: `"text"` | `"boolean"` | `"select"`
- `options`: list of valid values (for select type)
- `default`: default value (if any)
- `supported_by`: list of tool names (e.g., `["claude-code"]`)

**Rationale:** Structured enough for the TUI to render appropriate widgets, simple enough to maintain. New tools just add entries or extend `supported_by` lists.

### 6. Skill scaffolding output

**Decision:** `creator.py` exposes a `create_skill()` function that:
1. Resolves the target directory (vault or project-local via tool adapter)
2. Creates `<target>/skills/<name>/SKILL.md` with YAML frontmatter and content
3. Returns a result dict with path and status (consistent with existing patterns like `import_artifacts`)

The `name` frontmatter field is auto-populated from the positional arg but can be overridden via `--name` / `-n` or edited in the TUI.

**Rationale:** Consistent with the existing vault structure (`vault/skills/<name>/SKILL.md`) and tool adapter destinations.

### 7. Textual as a dependency

**Decision:** Add `textual>=0.50` to `pyproject.toml` dependencies.

**Rationale:** Textual is the most capable Python TUI framework, actively maintained, and aligns with the project's future plans to add TUI affordances to other commands. The transitive dependency cost (rich, etc.) is acceptable given that Artifactr is a CLI tool where users expect terminal capabilities.

## Risks / Trade-offs

- **Dependency weight**: Textual + rich is a significant jump from "just PyYAML". Users who only want non-interactive mode still install it.
  → Mitigation: Could make textual an optional dependency (`pip install artifactr[tui]`) in the future if this becomes a concern. For now, keep it simple with a hard dependency.

- **Textual version stability**: Textual's API has evolved rapidly.
  → Mitigation: Pin a minimum version, use stable widget APIs only (Input, TextArea, Button, Select, Switch, Static).

- **Known fields maintenance**: As tools evolve, the registry can become stale.
  → Mitigation: The registry is a single file, easy to update. Unknown fields are always available via custom field input.

- **Cross-platform TUI**: Textual works differently on Windows (limited mouse support, different terminal capabilities).
  → Mitigation: Textual handles this internally. Non-interactive mode is always available as fallback.
