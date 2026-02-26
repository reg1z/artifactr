## Context

Artifactr's business logic is split across decoupled modules (`catalog.py`, `config.py`, `creator.py`, `importer.py`, etc.) with all CLI parsing and handler dispatch in `cli.py`. External dependencies are limited to PyYAML. Vault export to zip already exists in `catalog.py` (`export_vaults()`, `import_vaults_from_zip()`), giving us a foundation for backup/restore. There is no existing mechanism for bundling files with the package or accessing them at runtime.

## Goals / Non-Goals

**Goals:**
- Bundle skill and command markdown files inside the Python package, accessible from any install method (PyPI, pipx, editable)
- Provide a single command (`art update-native-skills` / `art uns`) to install built-in skills into a project or globally
- Provide `art config backup` and `art config restore` for full-catalog portability
- Keep PyYAML as the only external dependency (no new packages)

**Non-Goals:**
- Versioned/incremental backups (one archive per invocation)
- Restoring absolute vault paths from the original machine
- Conflict resolution UI beyond simple name incrementing on restore
- Tool-specific frontmatter variants per skill (skills use generic YAML frontmatter)

## Decisions

### D1: Package data via `importlib.resources`

Built-in skills are stored as static files under `src/artifactr/builtin_skills/` and accessed at runtime via `importlib.resources.files("artifactr") / "builtin_skills"`. This is the standard cross-platform approach for Python package data since 3.9 and works across editable installs, PyPI wheels, and zipapp bundles.

`pyproject.toml` gains:
```toml
[tool.setuptools.package-data]
"artifactr" = ["builtin_skills/**/*"]
```

**Alternative considered**: Generating skills from Python string constants at runtime. Rejected — makes authoring awkward and diffs noisy.

### D2: Built-in skill directory structure mirrors vault layout

```
src/artifactr/builtin_skills/
  skills/
    artifactr-context/artifact.md
    art-create-skill/artifact.md
    art-create-cmd/artifact.md
    art-create-agent/artifact.md
  commands/
    art-create-skill.md
    art-create-cmd.md
    art-create-agent.md
```

`skills/` uses the directory-per-skill layout that Claude Code and OpenCode expect. `commands/` contains flat `.md` files. Using the same structure as the vault means the copy logic is identical regardless of source.

**Alternative considered**: A single monolithic skill file. Rejected — granular skills let users import only what they need.

### D3: New `builtins.py` module

A dedicated `src/artifactr/builtins.py` module encapsulates all `importlib.resources` access and the copy logic for installing built-in skills. The CLI handler calls into it; no resource-path logic leaks into `cli.py`.

Key functions:
- `get_builtin_skills_root() -> Traversable` — returns the `importlib.resources` path object
- `install_builtin_skills(target_skills_dir, target_commands_dir, overwrite=True) -> dict` — copies skills and commands, returns counts

### D4: `art update-native-skills` uses same tool resolution as `art proj import`

The command resolves the target directories using the existing `GenericToolAdapter` paths (same as `art proj import` / `art conf import`). For local installs, `adapter.get_path("skills")` and `adapter.get_path("commands")` relative to CWD. For `--global`, `adapter.get_global_path("skills")` etc.

This means `--tools` works the same way it does elsewhere in the CLI — comma-separated or repeatable, defaults to the configured default tool.

### D5: Git repo check for local `update-native-skills`

When installing to CWD (not `--global`), the command checks whether CWD is a git repo using the existing `is_git_repo()` utility. If not, it prompts `Y/n` before continuing. This mirrors the confirmation pattern elsewhere in the CLI.

### D6: Backup format extends existing `export_vaults()` zip structure

`art config backup` reuses the `export_vaults()` zip layout (vault dirs + `manifest.yaml`) and adds one additional entry: `config_snapshot.yaml`. This snapshot contains:

```yaml
format_version: 1
created_at: "2026-02-26T..."
default_vault_name: "personal"   # name, not absolute path
default_tool: opencode
nav_mode: null
tools: {}                        # custom tool definitions
```

`default_vault` is stored as a **name** (not a path) so it can be remapped to the new extracted path on restore.

**Alternative considered**: A separate `catalog.yaml` alongside the zip. Rejected — keeping everything in one file is simpler to transport.

### D7: Restore always extracts to `~/.config/artifactr/vaults/`

Restored vaults are always placed in the standard config-dir vaults directory, regardless of where they originally lived. This avoids needing path remapping UI and makes restore behavior predictable across machines.

### D8: Name conflict resolution: increment suffix

On restore, if a vault name from the archive conflicts with an already-registered vault name, the restore logic appends `-1`, `-2`, etc. until a unique name is found. No user prompt — restore proceeds and reports the remapping in the output.

### D9: Business logic in `catalog.py`

Two new functions: `backup_catalog(output_path) -> dict` and `restore_catalog(archive_path) -> dict`. These live in `catalog.py` alongside `export_vaults()` and `import_vaults_from_zip()` which they build on. No new module needed.

### D10: Skill frontmatter includes `version: 0.1`

All built-in skill `artifact.md` files include a `version: 0.1` frontmatter field alongside standard fields (e.g., `description`). This allows future `art update-native-skills` invocations to detect outdated installed copies.

## Risks / Trade-offs

- **`importlib.resources` traversal in editable installs** → `importlib.resources.files()` works correctly for editable installs in Python 3.10+ when `find_namespace_packages` or `find_packages` is used. The existing `setuptools.packages.find` config is compatible.
- **Skill content drift** → Built-in skills document config paths and command syntax that will change over time. Mitigated by the `version` frontmatter field and future `art update-native-skills` upgrades overwriting stale copies.
- **Backup does not validate vault health** → If a vault directory has been partially deleted, the backup will include whatever exists. No mitigation planned; this is expected behavior.
- **Restore skips if destination name conflicts** on path (not just name) → Current `import_vaults_from_zip()` checks for path conflicts; restore logic builds on this and additionally checks name conflicts with auto-rename.

## Migration Plan

No migration required. All changes are additive:
- New package data directory (no effect on existing installs until `update-native-skills` is run)
- New CLI commands (`update-native-skills`, `config backup`, `config restore`) alongside existing ones
- Version bump is backward-compatible

The stale test assertion in `test_project_structure.py` is fixed as part of the version bump task.

## Open Questions

None — all design decisions resolved during exploration.
