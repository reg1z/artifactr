---
spec: specs/v3_features_spec.md
---

# v3 Features Implementation Plan

## Phase 1: Tool Adapter — `get_global_destination()`

- [x] **Task 1**: Add abstract `get_global_destination(self, artifact_type: str) -> Path` method to `ToolAdapter` in `src/artifactr/tools/base.py`. Same pattern as `get_destination()` but takes no `target_repo` — returns the user-wide global path.

- [x] **Task 2**: Implement in `ClaudeCodeAdapter` (`src/artifactr/tools/claude_code.py`). Returns `~/.claude/<artifact_type>`.

- [x] **Task 3**: Implement in `OpenCodeAdapter` (`src/artifactr/tools/opencode.py`). Returns `~/.config/opencode/<artifact_type>`.

## Phase 2: `--force` flag

- [x] **Task 4**: Add `force: bool = False` parameter to `copy_with_prompt()` in `src/artifactr/importer.py`. When `force=True`, skip `prompt_overwrite()` and overwrite directly. Pass `force` through the recursive directory branch. Also add `force` parameter to `import_artifacts()` and pass it through to both `copy_with_prompt()` call sites.

## Phase 3: CLI wiring

- [x] **Task 5**: Update `create_parser()` in `src/artifactr/cli.py`:
  - Make `target` optional (`nargs="?"`, `default=None`).
  - Add `--global` / `-g` flag (`dest="global_import"`).
  - Add `--force` / `-f` flag.

- [x] **Task 6**: Update `handle_import()` in `src/artifactr/cli.py`:
  - Validate: if not `global_import` and `target` is None, error out.
  - If `global_import`, call `import_artifacts_global()`. Otherwise call `import_artifacts()` with `force`.
  - Add `import_artifacts_global` to the module imports from `.importer`.

## Phase 4: Global import logic

- [x] **Task 7**: Create `import_artifacts_global()` in `src/artifactr/importer.py`. Mirrors `import_artifacts()` but:
  - No `target` param, no git repo validation, no `add_to_git_exclude()`.
  - Uses `tool_adapter.get_global_destination(artifact_type)` for destinations.
  - Add `prompt_create_directory(path)` helper. Before copying to a destination dir, if it doesn't exist, prompt user to create it. If declined, skip that type/tool.
  - Tracks imports to the global cache file at `~/.config/artifactr/.art-cache-global/imported` using the same `<vault-label>.<tool>.<artifact>` line format as `update_import_cache()`. Create a new `update_global_import_cache()` function (or parameterize the existing one) that writes to `~/.config/artifactr/.art-cache-global/imported` instead of `<target>/.art-cache/imported`.
  - Returns the same result dict shape as `import_artifacts()`.

## Phase 5: Manual testing

- [x] **Task 8**: Verify: `art import ./repo --force` overwrites without prompts, still updates `.art-cache` and `.git/info/exclude`.
- [x] **Task 9**: Verify: `art import --global --tools=claude-code` imports to `~/.claude/{skills,agents,commands}` and writes to `~/.config/artifactr/.art-cache-global/imported`.
- [x] **Task 10**: Verify: `--global` prompts to create missing directories; `--force` does not suppress this prompt.
- [x] **Task 11**: Verify: `art import` (no target, no `--global`) errors with a helpful message.
- [x] **Task 12**: Verify: `--global` with `--artifacts`, `--vault`, `--link`, and `--force` combinations work correctly.
