# AGENTS.md

## Project Overview

**Artifactr** is a local-first CLI tool (`art`) for managing AI coding agent artifacts (skills, commands, agents) across projects. Users store artifacts in named **vaults**, then import them into any project as copies or symlinks. PyYAML is the only external dependency (`art update` makes a single outbound PyPI request).

## Tech Stack

- **Language**: Python 3.10+ (modern union syntax `str | None`, `list[str]`)
- **CLI framework**: `argparse` (stdlib only)
- **YAML**: PyYAML >= 6.0
- **Build**: `setuptools` via `pyproject.toml`
- **Tests**: `pytest` (566 tests in `tests/`)
- **Entry point**: `art` → `artifactr.cli:main`
- **Dev install**: `pip install -e .` (`.venv/` with Python 3.14)

## Commands

```sh
pytest                        # run all tests
python -m pytest tests/       # same
art --help                    # CLI reference
python -m build               # build wheel + sdist
```

## Directory Structure

```
src/artifactr/
  __main__.py     # Enables `python -m artifactr`; delegates to cli.main()
  cli.py          # All CLI logic: handle_* functions, main(), _main() ~5290 lines
  catalog.py      # Vault CRUD: add/remove/init/select/rename/list
  config.py       # Read/write ~/.config/artifactr/config.yaml and vault.yaml
  creator.py      # Artifact creation, edit-target resolution
  importer.py     # Copy/symlink artifacts, .art-cache management, link/unlink
  scanner.py      # Artifact discovery across dirs/vaults/global config paths
  updater.py      # Self-update logic: install detection, PyPI check, upgrade, PATH repair
  utils.py        # Cross-platform config/data dir, editor resolution, git detection
  known_fields.py # Registry of YAML frontmatter fields (KnownField dataclass)
  tools/
    __init__.py   # BUILTIN_TOOLS dict, tool registry, GenericToolAdapter factory
    base.py       # GenericToolAdapter class

tests/            # 18 test files, ~566 tests
openspec/         # Spec-driven dev artifacts (specs/ and changes/)
art/              # The project's own vault (dogfooding)
dist/             # Built wheels and sdists
```

## Architecture

**Decoupled CLI / business logic**: `cli.py` handlers call into dedicated modules. Every handler returns an int exit code (0 = success, 1 = failure). Business logic functions return structured dicts: `{"success": bool, "error": str | None, ...}` or `{"added": [...], "skipped": [...], "errors": [...]}`.

**Three-tier tool resolution**: `BUILTIN_TOOLS` < global `config.yaml` tools < vault `vault.yaml` tools. Higher tiers fully replace lower tiers for the same tool name. Tools are config-driven dicts — no hardcoded tool classes.

**`GenericToolAdapter`** (`tools/base.py`): wraps a tool definition dict. Derives supported artifact types from which keys are present (`skills`, `commands`, `agents`). Handles env var and `~` expansion in paths.

## Key Data Models

**Artifact dict**:
```python
{"name": str, "type": str, "type_plural": str, "path": Path, "tool": str, "config_dir": str}
```

**Tool definition dict**:
```python
{
    "aliases": ["claude"],
    "skills": ".claude/skills",          # repo-relative
    "commands": ".claude/commands",
    "agents": ".claude/agents",
    "global_skills": "$HOME/.claude/skills",
    "global_commands": "$HOME/.claude/commands",
    "global_agents": "$HOME/.claude/agents",
}
```

**Import cache entry** (`.art-cache/imported`):
```
[vault_paths]
label=/absolute/path/to/vault

[imported]
vault-label.tool-name.artifact-name:linked
```
Supports both legacy (no headers) and v2 format via `_parse_cache_file()`.

## Configuration

- **Global config**: `~/.config/artifactr/config.yaml` (Linux/XDG), `~/Library/Application Support/artifactr/config.yaml` (macOS), `%APPDATA%/artifactr/config.yaml` (Windows). `get_config_dir()` in `utils.py` handles all three.
- **Data dir** (install state): `~/.local/share/artifactr/` (Linux), same as config dir on macOS/Windows. `get_data_dir()` in `utils.py`. The managed venv and `.install-info` state file live here.
- **Per-vault config**: `vault.yaml` in vault root — name + tool overrides travel with the vault.
- **Project import cache**: `<project>/.art-cache/imported`
- **Global import cache**: `~/.config/artifactr/.art-cache-global/imported`
- **Git exclude**: Artifact paths written to `.git/info/exclude` (not `.gitignore`) on import.

## Conventions

- **Type hints on every function**.
- **CLI aliases**: Top-level `art -V`/`--version`; subcommand `-V`/`--vault` accepts comma-separated or repeated flags; extensive short aliases (`s`/`sk` skill, `c`/`cmd` command, `a`/`agt` agent; `cr` create, `ed` edit, `sp` spelunk, `st` store, `v` vault, `p`/`proj` project)
- **Slash syntax for `create`**: `art create skill/my-skill` is equivalent to `art create skill my-skill`, consistent with `edit`, `cat`, `inspect`, `export`, and `ls`.
- **Alias maintenance**: When adding, changing, or removing command aliases, both the argparse `aliases=` and the `make_help(aliases=...)` call must be updated. The `--help` output is the user-facing source of truth for discoverability.
- **Windows symlink fallback**: `create_link()` falls back to hard links when symlinks fail (requires both files on same volume)
- **Frontmatter name resolution**: All artifact name-matching commands MUST resolve names in this order: (1) exact filename/dirname match, (2) frontmatter `name:` field fallback. This convention applies project-wide — not just `art edit`. `_find_by_frontmatter_name()` and `_parse_frontmatter_name()` in `creator.py` are the canonical implementations.
- **Spec-driven dev**: Features are developed against specs in `openspec/changes/`. openspec tools are used in this repo.
- When updating README.md, edit only lines under the "Extended Usage" heading. No content above it should be touched.

## Help Text Format

Every `add_parser()` call uses `**make_help(...)` to produce consistent help output. `make_help()` is defined in `cli.py` and returns `description`, `epilog`, and `formatter_class` kwargs.

**Parameters:**
- `summary` (required): 1–2 sentence description of the command. Appears as the first paragraph in `--help`.
- `aliases` (optional): List of argparse aliases for this parser. Displayed as "Aliases: x, y" in the description block.
- `workflows` (optional): Step sequence string using `→` separator. Rendered under a "Workflows:" header in the epilog.
- `see_also` (optional): List of `(command, description)` tuples for laterally related commands. Rendered under "See Also:" in the epilog.
- `notes` (optional): 1–2 sentence caveat or important default. Rendered under "Notes:" in the epilog.

**Rendered sections** (epilog, separated by blank lines): Workflows → See Also → Notes.

## Key Workflows

**Import** (`art proj import`): resolves vault paths → calls `import_artifacts()` → copies or symlinks per tool/type → updates `.art-cache/imported` → writes to `.git/info/exclude`.

**Link** (`art proj link`): reads cache → finds vault source + project dest → replaces copy with symlink (backup on conflict) → updates cache `:linked` suffix.

**Spelunk** (`art spelunk`): defaults to CWD when no target is given; use `-g`/`--global` to spelunk global config dirs. Discovers artifacts → annotates with import status → outputs as human/JSON/YAML/Markdown.

**Store** (`art store`): discovers artifacts in target dir → user selects → copies into vault's `skills/`/`commands/`/`agents/` subdirs.

**Update** (`art update` / `art upgrade`): detects install method (editable, pipx, managed venv, unknown) → checks PyPI for latest version → confirms with user → runs upgrade subprocess → verifies result via `pip show` → optionally repairs PATH for venv installs.
