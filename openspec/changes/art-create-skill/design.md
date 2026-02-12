## Context

Artifactr currently supports discovering, storing, and importing artifacts but has no creation flow. Users must manually create directories and write YAML frontmatter. The codebase follows a pattern of decoupled business logic (catalog.py, importer.py, scanner.py) with CLI handlers in cli.py and tool-specific behavior in tools/. The only external dependency is PyYAML.

This change adds `art create skill <name>` with two modes: a Textual TUI for interactive creation, and a flag-based non-interactive mode. It introduces `textual` as a new dependency.

## Goals / Non-Goals

**Goals:**
- Scaffold skills in vaults or project-local tool directories with correct structure
- Provide a guided TUI experience that teaches users about available frontmatter fields
- Support non-interactive creation via flags for scripting and automation
- Maintain the tool-agnostic philosophy — no tool picker in the TUI, compatibility is informational only
- Keep the known-fields registry extensible as new tools are added

**Non-Goals:**
- Creating agents or commands (future work — only skills for now)
- Editing existing skills
- TUI for other commands (future work — only `art create` for now)
- Validating tool-specific field values (the TUI informs, it doesn't enforce)

## Decisions

### 1. Module structure

**Decision:** Three new modules in `src/artifactr/`:
- `creator.py` — Business logic for skill scaffolding (frontmatter generation, file writing, path resolution)
- `tui.py` — Textual app for interactive creation
- `known_fields.py` — Registry of known frontmatter fields with metadata (description, type, supported tools, input widget hint)

**Rationale:** Follows the existing pattern of decoupled logic. `creator.py` handles the "what" (building the SKILL.md content and writing it), `tui.py` handles the interactive "how", and `known_fields.py` is a pure data module that both the TUI and future help/docs features can reference. The CLI handler in cli.py orchestrates: it decides which mode to use and calls either the TUI or creator directly.

**Alternative considered:** Putting known fields inside the TUI module. Rejected because the field registry is useful beyond the TUI (e.g., `--help` text, future validation, documentation generation).

### 2. Non-interactive flag design (Option C hybrid)

**Decision:** First-class flags for common fields (`-n/--name`, `-d/--description`, `-c/--content`), plus `-D/--field key=value` (repeatable) for arbitrary frontmatter.

**Rationale:** `description` is always needed and deserves proper help text. Arbitrary fields via `-D` avoid polluting the argparse namespace with every possible frontmatter key while keeping the syntax clean. The `-D` convention is well-established from Java/Maven/CMake for arbitrary key-value pairs.

**Alternative considered:** `parse_known_args()` to allow any `--key value` flag. Rejected due to ambiguity (system flags vs frontmatter fields) and complexity.

### 3. Mode detection

**Decision:** If any of `--name`, `--description`, `--content`, or `--field` are provided, use non-interactive mode. Otherwise, launch the Textual TUI. No explicit `--interactive` / `--no-tui` flag.

**Rationale:** Presence of content flags is a natural, unambiguous signal. Users scripting will always provide flags; users exploring will type just `art create skill my-skill` and get the TUI. An explicit flag adds noise for no real gain.

### 4. Textual TUI structure

**Decision:** A single Textual `App` with a form layout:
- Pre-populated `Name` input (from positional arg, editable)
- `Description` text input
- `[+ Add Field]` button that opens a modal picker
- `Content` textarea for the markdown body
- `[Cancel]` and `[Create]` action buttons

The field picker modal shows:
1. Custom field name input (at top)
2. Known fields list below (with descriptions and tool compatibility)

Selecting a known field adds it to the form with the appropriate widget (text input, checkbox for booleans, select for enums like `context`). Each added field shows a tooltip icon with its description and which tools support it.

**Rationale:** Minimal default view keeps the form clean. The picker makes fields discoverable without overwhelming. Custom-first ordering reinforces tool-agnostic philosophy.

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
