---
plan: plans/v3_features_plan.md
---

# v3 Features Specification

## Overview

This spec adds two enhancements to the `art import` command:

1. **Global import mode** (`--global` / `-g`) — Import artifacts into a tool's user-wide global config directories instead of a local git repository.
2. **Force overwrite** (`--force` / `-f`) — Skip per-file overwrite confirmations during import.

---

## Feature 1: Global Import (`--global` / `-g`)

### 1.1 Purpose

Currently, `art import` copies artifacts into a target git repository's local config directories (e.g., `<repo>/.claude/skills/`). The `--global` flag adds the ability to import artifacts into a tool's **user-wide global config directories** — the directories each tool reads from regardless of which project is open.

### 1.2 Usage

```bash
# Import all vault artifacts globally for the default tool
art import --global

# Import globally for a specific tool
art import --global --tools=claude-code

# Import globally for multiple tools
art import --global --tools=claude-code,opencode

# Import specific artifacts globally
art import --global --artifacts=helping-hand,specout

# Combine with other existing flags
art import --global --vault=my-vault --tools=claude-code --artifacts=specout
```

### 1.3 Global Config Directory Mapping

Each tool defines where its global config directories live. These are the **user-wide** (not per-project) directories:

| Tool | Artifact Type | Global Directory |
|------|--------------|-----------------|
| claude-code | skills | `~/.claude/skills` |
| claude-code | agents | `~/.claude/agents` |
| claude-code | commands | `~/.claude/commands` |
| opencode | skills | `~/.config/opencode/skills` |
| opencode | agents | `~/.config/opencode/agents` |
| opencode | commands | `~/.config/opencode/commands` |

### 1.4 Requirements

1. **R1**: A new `--global` / `-g` flag is added to the `art import` command.
2. **R2**: When `--global` is used, the `target` positional argument becomes optional and is ignored if provided.
3. **R3**: When `--global` is used, the tool's global config directory is used as the import destination instead of a local repo path.
4. **R4**: All artifact types (skills, agents, commands) are imported by default — the same behavior as a normal import.
5. **R5**: The `--tools` flag determines which tool(s) to import for. If not provided, the default tool is used (same as normal import).
6. **R6**: The `--vault` flag works the same as in normal import — selects which vault to import from.
7. **R7**: The `--artifacts` flag works the same as in normal import — selects specific artifacts to import.
8. **R8**: The `--link` flag works the same as in normal import — creates symlinks instead of copies.
9. **R9**: If a global config directory does not exist, the user is prompted: `Directory does not exist: <path>\nCreate it? [y/N]: `. If the user declines, that directory is skipped.
10. **R10**: When `--global` is used, git-specific operations are **skipped**:
    - No `.git/info/exclude` management (there's no git repo).
    - No `.art-cache/imported` tracking (there's no target repo to track in). INSTEAD, a tracking file will be kept in the artifactr global config folder under `.config/artifactr/.art-cache-global/imported`
    - No git repository validation on the target.
11. **R11**: Overwrite prompting (per-file confirmation) still applies during global import, the same as normal import.
12. **R12**: The import summary output is the same format as normal import (tool name, artifact type, count).
13. **R13**: For `--global` imports, a tracking file should be kept in the artifactr global config folder under `.config/artifactr/.art-cache-global/imported` (as opposed to `.art-cache/imported` used in repo imports)


### 1.5 Tool Adapter Changes

Each tool adapter (`ToolAdapter` base class) needs a new method:

```python
def get_global_destination(self, artifact_type: str) -> Path:
    """Return the global config path for an artifact type."""
```

- **claude-code**: Returns `Path.home() / ".claude" / artifact_type`
- **opencode**: Returns `Path.home() / ".config" / "opencode" / artifact_type`

This is separate from the existing `get_destination()` method, which takes a `target_repo` path and returns a per-project destination.

### 1.6 Error Handling

- If `--global` is used and the user declines directory creation for all tools/types, the command completes with "No artifacts to import."
- If `--global` is used with an invalid vault, the same vault validation errors apply.
- If `--global` is used with an unsupported tool name in `--tools`, the same tool validation errors apply.

---

## Feature 2: Force Overwrite (`--force` / `-f`)

### 2.1 Purpose

Currently, when `art import` encounters a file that already exists at the destination, it prompts the user: `File already exists: <path>\nOverwrite? [y/N]:`. The `--force` flag skips this confirmation and overwrites all conflicting files automatically.

### 2.2 Usage

```bash
# Force import into a repo, overwriting existing files
art import ./my-repo --force

# Force global import
art import --global --force

# Short flag
art import ./my-repo -f
```

### 2.3 Requirements

1. **R13**: A new `--force` / `-f` flag is added to the `art import` command.
2. **R14**: When `--force` is used, the per-file overwrite prompt (`File already exists: ... Overwrite? [y/N]:`) is skipped. Existing files are silently overwritten.
3. **R15**: The `--force` flag only applies to `art import`. It is **not** added to `art store`.
4. **R16**: The `--force` flag works in combination with all other import flags (`--global`, `--tools`, `--vault`, `--artifacts`, `--link`).
5. **R17**: When `--force` is used, the import summary still reports counts accurately (files overwritten count as "imported", not "skipped").
6. **R18**: The directory creation prompt from `--global` (R9) is **not** affected by `--force`. The user is still prompted to confirm directory creation even when `--force` is set. `--force` only controls file-level overwrite behavior.

### 2.4 Implementation Detail

The `copy_with_prompt()` function in `importer.py` currently calls `prompt_overwrite()` when a destination file exists. A new `force` parameter (default `False`) is added:

- When `force=True`: skip `prompt_overwrite()`, delete the existing file, and copy/symlink the new one.
- When `force=False`: current behavior (prompt the user).

---

## Interaction Between Features

The `--global` and `--force` flags can be used together:

```bash
art import --global --force --tools=claude-code
```

This imports all artifacts from the default vault into `~/.claude/skills/`, `~/.claude/agents/`, and `~/.claude/commands/`, overwriting any existing files without confirmation. The directory creation prompt (R9) still appears if the directories don't exist.
