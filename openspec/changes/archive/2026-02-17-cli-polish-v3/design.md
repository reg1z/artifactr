## Context

Artifactr is a Python CLI tool (`art`) using argparse for command routing. The codebase separates CLI parsing (`cli.py`) from business logic (`catalog.py`, `creator.py`, `importer.py`, `scanner.py`). This change is a UX polish pass touching many commands but introducing no new architectural patterns — all changes fit cleanly into existing structures.

## Goals / Non-Goals

**Goals:**
- Reduce friction for common operations (shorthand flags, more aliases)
- Make the tool usable outside git repositories (project import)
- Add structured output for spelunk to enable scripting and tooling
- Add depth-controlled discovery for finding artifacts in non-vault directories
- Establish the `--yes`/`-y` pattern for confirmation prompts

**Non-Goals:**
- Adding new top-level commands
- Changing the underlying data model or config format
- HTML output for spelunk (roadmap item, not this change)
- Name→path index caching for frontmatter resolution
- Duplicate frontmatter `name` detection/warnings

## Decisions

### 1. Frontmatter name resolution: folder-first, frontmatter-fallback

**Decision:** When `art edit` resolves an artifact name, try folder/file match first. Only scan frontmatter `name` fields if no folder match is found.

**Rationale:** This is backwards-compatible (existing folder-based lookups unchanged), avoids unnecessary YAML parsing in the common case, and provides a natural fallback for users who only know the display name.

**Implementation:** Parse frontmatter by reading lines until the closing `---` delimiter. Extract only the `name` field. On multiple frontmatter matches, use the first found (alphabetical filesystem order). Apply to all artifact types (skills, agents, commands).

**Alternative considered:** Always scan frontmatter and error on ambiguity. Rejected — adds complexity and breaks the simple case where users just want to edit by folder name.

### 2. `--yes`/`-y` as "auto-confirm" (not "accept defaults")

**Decision:** The `--yes`/`-y` flag answers "yes" to all Y/n confirmation prompts. It does not imply "accept default values" for multi-choice prompts.

**Rationale:** Aligns with the convention established by `apt-get -y`, `terraform -auto-approve`, and similar tools. The current use cases (directory creation, non-git import) are all Y/n confirmations.

### 3. Spelunk output: format flag with four formats

**Decision:** Add `--format` accepting `human` (default), `json`, `yaml`, `md`/`markdown`. Each format receives the same underlying data structure.

**Implementation:** Spelunk handlers already collect artifact data into dicts. Add a formatting layer that serializes the same data structure into the requested format. The `md` format renders a markdown table. `json` uses `json.dumps`, `yaml` uses PyYAML's `yaml.dump`.

**Alternative considered:** Separate `--json` and `--yaml` flags. Rejected — a single `--format` flag is more extensible and prevents flag proliferation.

### 4. Spelunk depth scanning: layer-3 discovery

**Decision:** When spelunk targets a non-vault directory, add a layer-3 scan that recursively searches (up to `--depth`, default 2) for directories named `skills/`, `agents/`, `commands/` containing artifact-shaped content (`.md` files or `SKILL.md` subdirectories).

**Implementation:** Add a `discover_artifacts_by_structure()` function in `scanner.py` that walks directories up to the specified depth, looking for the standard artifact directory names and their expected contents. This runs after vault detection and tool-config scanning as a fallback layer.

### 5. Store `--global` flag: mutually exclusive with positional target

**Decision:** `--global`/`-g` and `target_dir` are mutually exclusive. If both are provided, error with a clear message.

**Implementation:** Make `target_dir` `nargs='?'` (optional). In the handler, validate that exactly one of `target_dir` or `--global` is provided.

### 6. Project import: soft git requirement

**Decision:** When target is not a git repo, prompt user with a Y/n confirmation instead of hard-erroring. If confirmed (or `--yes`), skip the `.git/info/exclude` step entirely.

**Rationale:** Users working outside git shouldn't be blocked. The exclude step is the only git-dependent behavior.

### 7. `-V` for `--vault`: applied universally

**Decision:** Add `-V` as a shorthand for `--vault` on every command that currently accepts `--vault`. No conflicts exist with any existing short flags.

## Risks / Trade-offs

- **[Frontmatter scanning performance]** → Mitigated by only scanning as fallback when folder match fails. Bounded to frontmatter section (until closing `---`), not full file reads.
- **[Depth scanning in large directories]** → Mitigated by default depth of 2 and respecting existing vault/tool-config detection (layer-3 only runs for non-vault, non-tool-config targets).
- **[Many small changes in one PR]** → Mitigated by the changes being independent and testable in isolation. Each can be implemented and verified separately.
