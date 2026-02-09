---
spec: specs/artifactr_spec.md
---

# Artifactr Implementation Plan

This document provides a step-by-step implementation plan for Artifactr. Tasks are ordered by dependency—complete earlier tasks before later ones.

## Project Structure

```
artifactr/
├── pyproject.toml          # Project metadata and entry point
├── src/
│   └── artifactr/
│       ├── __init__.py
│       ├── __main__.py     # Entry point: python -m artifactr
│       ├── cli.py          # CLI parsing with argparse
│       ├── config.py       # Configuration loading/saving
│       ├── catalog.py      # Vault catalog operations
│       ├── importer.py     # Import logic
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── base.py     # Base tool adapter class
│       │   ├── claude_code.py
│       │   └── opencode.py
│       └── utils.py        # Cross-platform helpers
├── tests/
│   └── ...
└── README.md
```

---

## Phase 1: Project Setup

### Task 1.1: Create project structure and pyproject.toml - [x] COMPLETE

Create the directory structure and configure the project for installation.

- Create all directories listed in the project structure above
- Create `pyproject.toml` with:
  - Project name: `artifactr`
  - Entry point script: `art = "artifactr.cli:main"`
  - Python version requirement: `>=3.8`
  - Dependency: `pyyaml` (for config file parsing)
- Create empty `__init__.py` files where needed

**Files to create:**
- `pyproject.toml`
- `src/artifactr/__init__.py`
- `src/artifactr/tools/__init__.py`

---

## Phase 2: Core Infrastructure

### Task 2.1: Implement cross-platform config path detection (`utils.py`) - [x] COMPLETE

Create a function that returns the correct configuration directory based on the operating system.

**Function:** `get_config_dir() -> Path`

**Logic:**
```python
# Pseudocode
if platform is Windows:
    return Path(os.environ.get('APPDATA')) / 'artifactr'
elif platform is macOS:
    return Path.home() / 'Library' / 'Application Support' / 'artifactr'
else:  # Linux and others
    # Respect XDG_CONFIG_HOME if set, otherwise use ~/.config
    xdg_config = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config:
        return Path(xdg_config) / 'artifactr'
    return Path.home() / '.config' / 'artifactr'
```

**Also add:**
- `is_git_repo(path: Path) -> bool`: Checks if a directory contains a `.git` folder

### Task 2.2: Implement configuration management (`config.py`) - [x] COMPLETE

Create functions to load and save the application configuration.

**Data structure:**
```yaml
# config.yaml
vaults:
  - /path/to/vault1
  - /path/to/vault2
default_vault: /path/to/vault1  # or null
```

**Functions to implement:**

- `get_config_path() -> Path`: Returns path to `config.yaml` (uses `get_config_dir()`)
- `load_config() -> dict`: Loads config from disk. If file doesn't exist, returns default empty config `{"vaults": [], "default_vault": None}`
- `save_config(config: dict) -> None`: Saves config to disk. Creates parent directories if they don't exist.

**Important:** Use `pathlib.Path` for all path operations. For YAML serialization, use `PyYAML` library. Add `pyyaml` as a dependency in `pyproject.toml`.

### Task 2.3: Implement vault catalog operations (`catalog.py`) - [x] COMPLETE

Create functions for managing the vault catalog. These functions contain the business logic, separate from CLI parsing.

**Functions to implement:**

- `add_vaults(paths: list[str]) -> dict`:
  - Takes a list of path strings
  - Validates each path exists and is a directory
  - Adds new vaults to config (skip duplicates)
  - If no default exists and vaults were added, set first new vault as default
  - Returns a result dict: `{"added": [...], "skipped": [...], "errors": [...]}`

- `remove_vaults(paths: list[str]) -> dict`:
  - Removes specified vaults from config
  - If removed vault was default, set `default_vault` to `None`
  - Returns a result dict: `{"removed": [...], "not_found": [...]}`

- `select_default(path: str) -> bool`:
  - Sets the specified vault as default
  - Returns `True` if successful, `False` if vault not in catalog

- `list_vaults() -> dict`:
  - Returns `{"vaults": [...], "default": "..." or None}`

- `get_default_vault() -> str | None`:
  - Returns the default vault path, or `None` if not set

- `get_vault_by_name_or_path(identifier: str) -> str | None`:
  - Returns the full vault path if found in catalog, else `None`
  - Matches by exact path or by the vault directory's basename

---

## Phase 3: Tool Adapters

### Task 3.1: Create base tool adapter class (`tools/base.py`) - [x] COMPLETE

Define an abstract base class that all tool adapters must implement.

**Key concept:** Vaults store artifacts in a tool-agnostic format. All tools read from the same source paths (`vault/skills/`, `vault/agents/`, `vault/commands/`). Each tool adapter only defines where artifacts should be written in the target repo.

```python
from abc import ABC, abstractmethod
from pathlib import Path

# Artifact types supported by all tools (tool-agnostic)
ARTIFACT_TYPES = ["skills", "agents", "commands"]

def get_source(artifact_type: str, vault_path: Path) -> Path:
    """Return the source path for an artifact type in the vault.

    This is a module-level function because sources are tool-agnostic.
    All tools read from the same vault structure.
    """
    return vault_path / artifact_type

class ToolAdapter(ABC):
    """Base class for tool-specific import logic.

    Each adapter defines only the DESTINATION paths for a specific tool.
    Source paths are tool-agnostic (see get_source function).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the tool's identifier (e.g., 'claude-code')."""
        pass

    @abstractmethod
    def get_destination(self, artifact_type: str, target_repo: Path) -> Path:
        """Return the destination path for an artifact type in the target repo."""
        pass
```

### Task 3.2: Implement claude-code adapter (`tools/claude_code.py`) - [x] COMPLETE

Create a concrete implementation of `ToolAdapter` for claude-code.

```python
from .base import ToolAdapter
from pathlib import Path

class ClaudeCodeAdapter(ToolAdapter):
    @property
    def name(self) -> str:
        return "claude-code"

    def get_destination(self, artifact_type: str, target_repo: Path) -> Path:
        return target_repo / ".claude" / artifact_type
```

### Task 3.3: Implement opencode adapter (`tools/opencode.py`) - [x] COMPLETE

Create a concrete implementation of `ToolAdapter` for opencode.

```python
from .base import ToolAdapter
from pathlib import Path

class OpenCodeAdapter(ToolAdapter):
    @property
    def name(self) -> str:
        return "opencode"

    def get_destination(self, artifact_type: str, target_repo: Path) -> Path:
        return target_repo / ".opencode" / artifact_type
```

### Task 3.4: Create tool registry (`tools/__init__.py`) - [x] COMPLETE

Create a registry that maps tool names to their adapter instances.

```python
from .base import ToolAdapter, ARTIFACT_TYPES, get_source
from .claude_code import ClaudeCodeAdapter
from .opencode import OpenCodeAdapter

# Registry of all supported tools
TOOL_REGISTRY: dict[str, ToolAdapter] = {
    "claude-code": ClaudeCodeAdapter(),
    "opencode": OpenCodeAdapter(),
}

def get_tool(name: str) -> ToolAdapter | None:
    """Get a tool adapter by name."""
    return TOOL_REGISTRY.get(name)

def get_supported_tools() -> list[str]:
    """Return list of all supported tool names."""
    return list(TOOL_REGISTRY.keys())

# Re-export for convenience
__all__ = ["ARTIFACT_TYPES", "get_source", "get_tool", "get_supported_tools"]
```

---

## Phase 4: Import Logic

### Task 4.1: Implement git exclude management (`importer.py`) - [x] COMPLETE

Create functions to manage the `.git/info/exclude` file.

**Functions:**

- `add_to_git_exclude(repo_path: Path, patterns: list[str]) -> None`:
  - Opens `.git/info/exclude` (create if doesn't exist)
  - Reads existing patterns
  - Adds new patterns that aren't already present
  - Each pattern should be on its own line
  - Add a header comment if this is the first artifactr entry: `# Added by artifactr`

### Task 4.2: Implement file copying with overwrite prompt (`importer.py`) - [x] COMPLETE

Create a function that copies files/directories with user confirmation for overwrites.

**Function:** `copy_with_prompt(src: Path, dst: Path) -> dict`

**Logic:**
- If `src` is a file:
  - If `dst` exists, prompt user: `File already exists: {dst}\nOverwrite? [y/N]: `
  - If user confirms (y/Y), overwrite; otherwise skip
  - Copy file to destination
- If `src` is a directory:
  - Recursively handle each file, prompting for each conflict
- Return dict with counts: `{"copied": n, "skipped": n}`

### Task 4.3: Implement main import function (`importer.py`) - [x] COMPLETE

Create the core import logic that orchestrates the import process.

**Function:** `import_artifacts(target: str, vault: str | None, tools: list[str] | None) -> dict`

**Key concept:** Sources are tool-agnostic. The same `vault/skills/my-skill/` directory gets copied to different destinations depending on which tools are selected (e.g., `.claude/skills/my-skill/` and `.opencode/skills/my-skill/`).

**Logic:**
1. Resolve `vault` to full path (use default if `None`)
2. Validate vault exists in catalog
3. Validate target is a git repository
4. Determine which tools to import (all supported tools if `tools` is `None`)
5. Validate all specified tools are supported
6. For each artifact type (skills, agents, commands):
   - Get source path from vault using `get_source(artifact_type, vault_path)`
   - If source exists and has contents:
     - For each selected tool:
       - Get destination path using `tool_adapter.get_destination(artifact_type, target_repo)`
       - Copy artifacts from source to destination
       - Track copied paths for git exclude
7. Add all imported paths to `.git/info/exclude`
8. Return result dict with summary

**Return structure:**
```python
{
    "success": True,  # or False if validation failed
    "errors": [],     # list of error messages
    "imported": {
        "claude-code": {"skills": 3, "agents": 1, "commands": 0},
        "opencode": {"skills": 3, "agents": 1, "commands": 0}  # same counts if same artifacts
    },
    "skipped": 2  # files user chose not to overwrite
}
```

---

## Phase 5: CLI Implementation

### Task 5.1: Create CLI skeleton with argparse (`cli.py`) - [x] COMPLETE

Set up the argument parser with subcommands.

```python
import argparse

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='art',
        description='Manage AI project artifacts across repositories'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # import command
    import_parser = subparsers.add_parser('import', help='Import artifacts into a git repo')
    import_parser.add_argument('target', help='Path to target git repository')
    import_parser.add_argument('--vault', help='Vault to import from (default: default vault)')
    import_parser.add_argument('--tools', help='Comma-separated list of tools to import')

    # vault command with subcommands
    vault_parser = subparsers.add_parser('vault', help='Manage vaults')
    vault_subparsers = vault_parser.add_subparsers(dest='vault_command')

    # vault add
    vault_add = vault_subparsers.add_parser('add', help='Add vaults to catalog')
    vault_add.add_argument('paths', nargs='+', help='Vault paths to add')

    # vault rm
    vault_rm = vault_subparsers.add_parser('rm', help='Remove vaults from catalog')
    vault_rm.add_argument('paths', nargs='+', help='Vault paths to remove')

    # vault select
    vault_select = vault_subparsers.add_parser('select', help='Set default vault')
    vault_select.add_argument('path', help='Vault path to set as default')

    # vault list
    vault_subparsers.add_parser('list', help='List all vaults')

    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()
    # Route to appropriate handler...
```

### Task 5.2: Implement CLI command handlers (`cli.py`) - [x] COMPLETE

Create handler functions that bridge CLI arguments to core logic.

**Handlers to implement:**

- `handle_import(args)`:
  - Parse `--tools` into list if provided
  - Call `import_artifacts()`
  - Print results or errors to stdout/stderr
  - Return appropriate exit code

- `handle_vault_add(args)`:
  - Call `add_vaults(args.paths)`
  - Print results

- `handle_vault_rm(args)`:
  - Call `remove_vaults(args.paths)`
  - Print results

- `handle_vault_select(args)`:
  - Call `select_default(args.path)`
  - Print confirmation or error

- `handle_vault_list(args)`:
  - Call `list_vaults()`
  - Print formatted output with default marker

### Task 5.3: Create entry point (`__main__.py`) - [x] COMPLETE

Allow running as `python -m artifactr`.

```python
from .cli import main

if __name__ == '__main__':
    main()
```

---

## Phase 6: Testing & Polish

### Task 6.1: Manual testing checklist - [x] COMPLETE

Test all commands work correctly:

- [x] `art vault add /path/to/vault` adds vault and sets as default
- [x] `art vault add /path/one /path/two` adds multiple vaults
- [x] `art vault list` shows all vaults with default marked
- [x] `art vault select /path/two` changes default
- [x] `art vault rm /path/one` removes vault
- [x] `art import /path/to/repo` imports from default vault to all tool destinations
- [x] `art import /path/to/repo --vault=name` imports from specific vault
- [x] `art import /path/to/repo --tools=claude-code` imports only to claude-code destinations
- [x] `art import /path/to/repo --tools=claude-code,opencode` imports same artifacts to both tool destinations
- [x] Import prompts before overwriting existing files
- [x] Imported paths appear in `.git/info/exclude`
- [x] Error messages display correctly for all invalid inputs

### Task 6.2: Test cross-platform paths - [x] COMPLETE

Verify on each platform (or document expected behavior):

- [x] Config directory created in correct location
- [x] Paths with spaces handled correctly
- [x] Path separators work correctly

### Task 6.3: Add helpful CLI output - [x] COMPLETE

Enhance user experience:

- Add `--version` flag showing version number
- Add `--help` text for all commands
- Use colors for success/error messages (optional, check if terminal supports it)
- Show progress during import (e.g., "Importing skills... done")

---

## Summary: Implementation Order

1. **Phase 1** - Project setup (Task 1.1)
2. **Phase 2** - Core infrastructure (Tasks 2.1 → 2.2 → 2.3)
3. **Phase 3** - Tool adapters (Tasks 3.1 → 3.2, 3.3 in parallel → 3.4)
4. **Phase 4** - Import logic (Tasks 4.1 → 4.2 → 4.3)
5. **Phase 5** - CLI (Tasks 5.1 → 5.2 → 5.3)
6. **Phase 6** - Testing and polish (Tasks 6.1 → 6.2 → 6.3)

Total: 15 tasks across 6 phases.
