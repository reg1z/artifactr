## 1. Import Cache V2

- [x] 1.1 Update `update_import_cache()` in `importer.py` to accept a `link_state` parameter (`:linked`, `:copied`, `:win_hardlinked`) and append the suffix to each entry
- [x] 1.2 Update `update_global_import_cache()` in `importer.py` with the same `link_state` parameter and suffix logic
- [x] 1.3 Add `[vault_paths]` section writing to both `update_import_cache()` and `update_global_import_cache()` — record `vault_label=vault_path` when importing
- [x] 1.4 Update `load_import_cache()` in `scanner.py` to parse v2 format: handle `[vault_paths]`/`[imported]` section headers, parse `:suffix` from entries, treat missing suffix as `:copied`, treat headerless files as all-`[imported]`
- [x] 1.5 Add a `update_cache_link_state()` function in `importer.py` that updates the suffix of a specific entry in `.art-cache/imported` (used by link/unlink commands)
- [x] 1.6 Add a `load_vault_paths_from_cache()` function in `importer.py` that reads the `[vault_paths]` section and returns a `dict[str, str]` mapping labels to paths

## 2. Core Linking Utilities

- [x] 2.1 Add `are_hardlinked(file_a: Path, file_b: Path) -> bool` utility function in `importer.py` using `os.stat()` to compare `st_dev` and `st_ino`
- [x] 2.2 Add `files_differ(path_a: Path, path_b: Path) -> bool` utility function in `importer.py` to compare file contents (for diff detection on link)
- [x] 2.3 Add `backup_artifact(artifact_path: Path, artifact_type: str, artifact_name: str, cache_dir: Path)` function in `importer.py` that copies an artifact to `.art-cache/backups/YYYY-MM-DD/<artifact_type>/<artifact_name>/`
- [x] 2.4 Add `create_link(src: Path, dst: Path) -> str` function in `importer.py` that creates a symlink (returns `"linked"`), with Windows fallback to `os.link()` after prompting (returns `"win_hardlinked"`). On non-Windows, always uses symlink.
- [x] 2.5 Add `resolve_artifact_patterns(patterns: list[str], cache_entries: list[dict]) -> list[dict]` function in `importer.py` using `fnmatch` to resolve names/globs against imported cache entries

## 3. Link/Unlink Logic

- [x] 3.1 Add `link_artifacts(target: Path, names: list[str], all_flag: bool, force: bool, vault_labels: list[str], type_filters: dict | None) -> dict` function in `importer.py` — filters by vault labels, resolves patterns, detects diffs, prompts/backs up, replaces copies with symlinks, updates cache
- [x] 3.2 Add `unlink_artifacts(target: Path, names: list[str], all_flag: bool, vault_labels: list[str], type_filters: dict | None) -> dict` function in `importer.py` — filters by vault labels, resolves patterns, reads content through link, replaces with copy, updates cache
- [x] 3.3 Add `link_artifacts_global(names: list[str], all_flag: bool, force: bool, vault_labels: list[str], type_filters: dict | None) -> dict` function in `importer.py` — same as 3.1 but for global config directories
- [x] 3.4 Add `unlink_artifacts_global(names: list[str], all_flag: bool, vault_labels: list[str], type_filters: dict | None) -> dict` function in `importer.py` — same as 3.2 but for global config directories

## 4. Update Existing Import Functions

- [x] 4.1 Update `import_artifacts()` call to `update_import_cache()` to pass `link_state="linked"` when `link=True`, `"copied"` otherwise
- [x] 4.2 Update `import_artifacts_global()` call to `update_global_import_cache()` to pass `link_state` similarly
- [x] 4.3 Update `copy_with_prompt()` to use `create_link()` instead of bare `dst.symlink_to()` when `link=True` (enables Windows fallback)

## 5. Store Graceful Skip

- [x] 5.1 In the `art store` handler in `cli.py`, before calling `copy_with_prompt()` for each artifact, check if the source is a symlink resolving to a path within the target vault — if so, skip with message

## 6. CLI Registration

- [x] 6.1 Register `link` subcommand (alias `ln`) under `proj` subparser with args: positional `names` (nargs='*'), `--all`/`-a`, `--force`/`-f`, `--vault`/`-V` (repeatable, comma-separated), type filters
- [x] 6.2 Register `unlink` subcommand (alias `uln`) under `proj` subparser with args: positional `names` (nargs='*'), `--all`/`-a`, `--vault`/`-V` (repeatable, comma-separated), type filters
- [x] 6.3 Register `link` subcommand (alias `ln`) under `conf` subparser with same args as 6.1
- [x] 6.4 Register `unlink` subcommand (alias `uln`) under `conf` subparser with same args as 6.2
- [x] 6.5 Add `handle_proj_link(args)` handler function in `cli.py`
- [x] 6.6 Add `handle_proj_unlink(args)` handler function in `cli.py`
- [x] 6.7 Add `handle_conf_link(args)` handler function in `cli.py`
- [x] 6.8 Add `handle_conf_unlink(args)` handler function in `cli.py`
- [x] 6.9 Update help text for `proj` and `conf` namespaces to include link/unlink commands

## 7. Vault-Scoped Operations

- [x] 7.1 Change `--vault`/`-V` on all 4 link/unlink commands to `action="append"` with comma-split support (repeatable flag)
- [x] 7.2 Add `--vault`/`-V` to both `unlink` commands (proj and conf) — was previously missing
- [x] 7.3 Add `_resolve_vault_scope()` helper in `cli.py` that resolves explicit `-V` values or falls back to the default vault label
- [x] 7.4 Update all 4 handlers (`handle_proj_link`, `handle_proj_unlink`, `handle_conf_link`, `handle_conf_unlink`) to pass `vault_labels: list[str]` instead of `vault: str | None`
- [x] 7.5 Update `link_artifacts()`, `unlink_artifacts()`, `link_artifacts_global()`, `unlink_artifacts_global()` to accept `vault_labels: list[str]` and filter entries by vault label before pattern matching

## 8. Windows Fallback Integration

- [x] 8.1 In `create_link()`, implement try/except around `symlink_to()` on Windows, prompt user for hard link fallback approval
- [x] 8.2 In `create_link()`, validate same-volume requirement before attempting `os.link()` — error with Developer Mode guidance if cross-volume
- [x] 8.3 Add clear messaging explaining the difference between symlinks and hard links when fallback is used
