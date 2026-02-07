---
spec: specs/v2_features_spec.md
---

# Artifactr v2 Features Implementation Plan

This plan implements the features described in [the v2 features spec](../specs/v2_features_spec.md). Tasks are ordered by dependency.

## Project Structure Changes

```
src/artifactr/
├── cli.py          # Modified — new flags, new command routing
├── catalog.py      # Modified — vault hierarchy listing
├── importer.py     # Modified — selective import, .art-cache tracking
├── scanner.py      # NEW — shared artifact discovery logic (spelunk + store)
└── tools/
    └── base.py     # Modified — add config_dir property to ToolAdapter
```

---

## Phase 1: Foundation — Tool Config Directory Mapping

### Task 1.1: Add `config_dir` property to `ToolAdapter` base class

The `art spelunk` and `art store` commands need to know which directories to probe in a target repo (e.g., `.claude/`, `.opencode/`). Currently, adapters only define destination paths. We need a way to derive the tool's config directory name.

- [x] Add a `config_dir` property to `ToolAdapter` (abstract base class in `tools/base.py`) that returns the tool's config directory name as a string (e.g., `".claude"`, `".opencode"`)
- [x] Implement it in `ClaudeCodeAdapter` (return `".claude"`) and `OpenCodeAdapter` (return `".opencode"`)
- [x] Add a module-level function `get_tool_config_dirs() -> dict[str, str]` in `tools/__init__.py` that returns a mapping of tool name to config dir name (e.g., `{"claude-code": ".claude", "opencode": ".opencode"}`)

**Files:** `src/artifactr/tools/base.py`, `src/artifactr/tools/claude_code.py`, `src/artifactr/tools/opencode.py`, `src/artifactr/tools/__init__.py`

---

## Phase 2: Artifact Discovery Module

### Task 2.1: Create `scanner.py` — shared artifact discovery logic

Both `art spelunk` and `art store` need to discover artifacts in a target directory. Extract this into a reusable module.

- [x] Create `src/artifactr/scanner.py`
- [x] Implement `discover_artifacts(target: Path) -> list[dict]`
  - Uses `get_tool_config_dirs()` from Task 1.1 to know which directories to search
  - For each tool config dir that exists in `target`:
    - Check `skills/` — any subdirectory containing a `SKILL.md` file is a skill artifact
    - Check `agents/` — any `.md` file directly inside is an agent artifact
    - Check `commands/` — any `.md` file directly inside is a command artifact
  - Return a list of dicts, each with:
    - `name`: artifact name (dir name for skills, filename without `.md` for agents/commands)
    - `type`: `"skill"`, `"agent"`, or `"command"` (singular)
    - `type_plural`: `"skills"`, `"agents"`, or `"commands"` (for path construction)
    - `path`: absolute Path to the artifact (directory for skills, file for agents/commands)
    - `tool`: tool name (e.g., `"claude-code"`)
    - `config_dir`: config dir name (e.g., `".claude"`)
  - Sort results by tool name, then type, then name

- [x] Implement `extract_description(artifact: dict) -> str`
  - Reads the main artifact file (SKILL.md for skills, the .md file for agents/commands)
  - Parses YAML frontmatter (delimited by `---` lines at the start of the file)
  - Returns the `description` value if present and non-empty
  - Truncates to 50 characters + `...` if too long
  - Returns `"-"` if no frontmatter, no description key, or empty value
  - Uses `yaml.safe_load()` for parsing

- [x] Implement `load_import_cache(target: Path) -> dict[str, list[str]]`
  - Reads `.art-cache/imported` from the target directory
  - Returns a dict mapping artifact names to lists of vault names they were imported from
  - Parses each line as `vault.tool.artifact` — extracts the vault (first segment) and artifact (last segment)
  - Returns empty dict if file doesn't exist

**Files:** `src/artifactr/scanner.py`

---

## Phase 3: `art vault list --all`

### Task 3.1: Add vault hierarchy listing to `catalog.py`

- [x] Add function `get_vault_hierarchy(vault_path: str) -> dict`
  - Takes a vault path string
  - Walks the vault directory (tool-agnostic structure: `skills/`, `agents/`, `commands/`)
  - Returns a dict like:
    ```python
    {
      "skills": ["helping-hand", "code-review"],
      "agents": ["reviewer.md"],
      "commands": []
    }
    ```
  - If the vault path doesn't exist on disk, return `None` (caller prints warning)

**Files:** `src/artifactr/catalog.py`

### Task 3.2: Add `--all` flag to CLI and update handler

- [x] In `create_parser()` in `cli.py`: add `-a`/`--all` flag to the `vault list` subparser
  - `action="store_true"`, `dest="show_all"`
- [x] Update `handle_vault_list()`:
  - If `args.show_all` is falsy, keep existing behavior unchanged
  - If `args.show_all` is truthy:
    - For each vault, call `get_vault_hierarchy()` from Task 3.1
    - Print tree-style indented output per spec §1.3:
      - Level 1 (4-space indent or `* ` prefix): vault name/path
      - Level 2 (6-space indent): artifact type headings (e.g., `skills/`) — only if type has items
      - Level 3 (8-space indent): individual artifact names (trailing `/` for skills)
    - If `get_vault_hierarchy()` returns `None`, print `(path not found)` next to the vault name

**Files:** `src/artifactr/cli.py`

---

## Phase 4: `.art-cache/imported` Tracking

### Task 4.1: Add import cache writing to `importer.py`

- [x] Add function `update_import_cache(target: Path, vault_path: str, vault_name: str | None, tool_name: str, artifact_names: list[str]) -> None`
  - Creates `.art-cache/` directory in `target` if it doesn't exist
  - Creates or appends to `.art-cache/imported`
  - For each artifact name, writes a line: `<vault-label>.<tool-name>.<artifact-name>`
    - `vault-label` = vault name if assigned, otherwise basename of vault path
  - Checks for duplicate lines before appending
- [x] Update `import_artifacts()` to call `update_import_cache()` after each tool's artifacts are imported
  - Collect artifact names as they are imported (the filesystem name, without extension for files)
  - Look up the vault name from config's `vault_names` dict
- [x] Update `add_to_git_exclude()` call to also include `.art-cache` pattern

**Files:** `src/artifactr/importer.py`

---

## Phase 5: `art import --artifacts`

### Task 5.1: Add artifact resolution logic to `importer.py`

- [x] Add function `resolve_artifact_names(vault_path: Path, artifact_specs: list[str]) -> list[dict]`
  - Takes the vault path and a list of artifact specifiers (e.g., `["helping-hand", "skills/write-thing"]`)
  - For each specifier:
    - If it contains a `/` (e.g., `skills/write-thing`), treat the part before `/` as the type prefix and search only that type
    - Otherwise, search all artifact types for a match
    - A match for skills: `vault/skills/<name>/` directory exists
    - A match for agents: `vault/agents/<name>.md` file exists
    - A match for commands: `vault/commands/<name>.md` file exists
  - If a name matches exactly one type, resolve it
  - If a name matches multiple types, prompt the user to pick one (per spec §2.2.4)
  - If a name matches nothing, print an error and skip it
  - Return a list of dicts: `{"name": str, "type": str, "source": Path}` for each resolved artifact

**Files:** `src/artifactr/importer.py`

### Task 5.2: Add `--artifacts` flag to CLI and update import logic

- [x] In `create_parser()`: add `--artifacts` flag to the `import` subparser
  - `help="Comma-separated list of artifact names to import"`
- [x] Update `import_artifacts()` to accept an optional `artifacts: list[str] | None` parameter
  - When `artifacts` is provided:
    - Call `resolve_artifact_names()` to get the list of resolved artifacts
    - Import only those specific artifacts (instead of iterating all artifact types)
    - For each resolved artifact, copy/symlink to each selected tool's destination
  - When `artifacts` is `None`: keep existing full-import behavior
- [x] Update `handle_import()` in `cli.py`:
  - Parse `args.artifacts` by splitting on commas and trimming whitespace
  - Pass to `import_artifacts()`

**Files:** `src/artifactr/cli.py`, `src/artifactr/importer.py`

---

## Phase 6: `art spelunk`

### Task 6.1: Add `spelunk` command to CLI

- [x] In `create_parser()`: add `spelunk` subparser
  - Positional arg: `target` (path to directory to probe)
- [x] Implement `handle_spelunk(args) -> int`:
  - Validate target exists and is a directory
  - Call `discover_artifacts()` from `scanner.py` (Task 2.1)
  - If no artifacts found, print `"No artifacts found in <target>"` and return 0
  - Call `load_import_cache()` to get import history
  - Call `extract_description()` for each artifact
  - For each artifact, check if its name appears in the import cache; if so, append `(imported: <vault1>, <vault2>)` to the name column
  - Format output as a table with dynamically-sized columns (NAME, TYPE, PATH, DESCRIPTION) with 2-space minimum padding between columns
  - Print the header row, then each artifact row
- [x] Add routing in `main()` for `args.command == "spelunk"`

**Files:** `src/artifactr/cli.py`

---

## Phase 7: `art store`

### Task 7.1: Add `store` command to CLI

- [x] In `create_parser()`: add `store` subparser
  - Positional arg: `target_dir` (path to directory containing artifacts)
  - Optional flag: `--vault` (vault to store into, defaults to default vault)
- [x] Implement `handle_store(args) -> int`:
  - Validate target exists and is a directory
  - Resolve vault (use `--vault` if provided, otherwise default vault)
  - Validate vault exists in catalog
  - Call `discover_artifacts()` from `scanner.py`
  - If no artifacts found, print message and return 0
  - Display numbered list of discovered artifacts
  - Prompt user for selection (support `1`, `1,3,5`, `1-3`, `all`, and combos like `1,3-5`)
  - Implement `parse_selection(input: str, max_val: int) -> list[int]` helper to parse the selection input into a list of 0-based indices
  - For each selected artifact:
    - Determine destination in vault: `<vault>/<type_plural>/<artifact_name>`
    - Copy using existing `copy_with_prompt()` from `importer.py` (handles overwrite prompting)
    - Print confirmation line
  - Print summary
- [x] Add routing in `main()` for `args.command == "store"`

**Files:** `src/artifactr/cli.py`

---

## Summary: Implementation Order

1. **Phase 1** — Tool config dir mapping (Task 1.1) — prerequisite for scanner
2. **Phase 2** — Scanner module (Task 2.1) — prerequisite for spelunk + store
3. **Phase 3** — Vault list --all (Tasks 3.1, 3.2) — independent feature, can be done in parallel with Phase 4
4. **Phase 4** — Import cache tracking (Task 4.1) — prerequisite for selective import and spelunk import detection
5. **Phase 5** — Import --artifacts (Tasks 5.1, 5.2) — depends on Phase 4
6. **Phase 6** — Spelunk command (Task 6.1) — depends on Phases 2 and 4
7. **Phase 7** — Store command (Task 7.1) — depends on Phases 2 and 6

Total: 8 tasks across 7 phases.
