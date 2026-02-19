## 1. art edit — Unified Specifier and Auto-Detection

- [x] 1.1 Refactor `art edit` parser to accept a single unified positional `artifact` (replacing separate `artifact_type` + `artifact_name`) while preserving backward compatibility with the old two-positional form
- [x] 1.2 Implement type auto-detection in `handle_edit`: scan default vault for artifact matching the name; error with disambiguation hint if multiple types match
- [x] 1.3 Implement `[type/]name[/sub/path]` specifier parsing: consume first segment as type alias if it's a known alias, second segment as artifact name, remaining segments as sub-path
- [x] 1.4 Add `-i` / `--interactive` flag to `art edit` parser
- [x] 1.5 Add `-m` / `--main` flag to `art edit` parser
- [x] 1.6 Add `-n` / `--new-file <path>` flag to `art edit` parser
- [x] 1.7 Update `make_help(aliases=...)` and help text for `art edit` to reflect new flags and specifier syntax

## 2. art edit — Sub-Path and New-File Support

- [x] 2.1 Implement sub-path resolution in `handle_edit`: given artifact dir + sub-path string, build the full path and verify it exists before opening in `$EDITOR`
- [x] 2.2 Implement `--new-file` behavior: create intermediate directories and file, error if path already exists, open in `$EDITOR`
- [x] 2.3 Error on sub-path or `--new-file` when the resolved artifact is file-based (command/agent)
- [x] 2.4 Write tests for sub-path resolution, `--new-file` creation, and error cases

## 3. art edit — Interactive File Picker

- [x] 3.1 Implement `_show_skill_picker(skill_dir: Path) -> Path | None` in `cli.py`: render numbered file tree, action keys (`n`, `d`, `i`, `q`), read input via `input()`, return selected path or None on quit
- [x] 3.2 Integrate picker into `handle_edit`: show picker when skill has files beyond `SKILL.md` (unless `-m` set); always show picker when `-i` set; skip picker when `sys.stdin.isatty()` is False
- [x] 3.3 Implement picker new-file action: prompt for relative path, create file + intermediate dirs, open in `$EDITOR`; error on collision
- [x] 3.4 Implement picker import-file action: prompt for source path with `~` expansion, prompt for optional destination relative path within skill, copy file, open in `$EDITOR`; error if source not found; confirm on destination collision
- [x] 3.5 Implement picker delete action: re-display file list for selection, confirm before deletion, disallow deleting `SKILL.md`, remove empty parent directories after deletion
- [x] 3.6 Implement picker invalid-index handling: re-show prompt with error message
- [x] 3.7 Write tests for picker logic (new-file, import, delete, SKILL.md deletion guard, non-TTY fallback)

## 4. art ls — Artifact File Listing

- [x] 4.1 Add optional `artifact_name` positional argument to the `art ls` parser (nargs="?")
- [x] 4.2 Implement artifact-name branch in `handle_list`: resolve artifact from default vault (or `-V` vault); if directory-based, list files with relative paths; if file-based, print error and exit 1
- [x] 4.3 Support `[type/]name` prefix syntax in the `artifact_name` argument (reuse specifier parsing from task 1.3)
- [x] 4.4 Display `SKILL.md` first with `(main)` label; display all other files with relative paths
- [x] 4.5 Write tests for `art ls <artifact-name>` including file-based error, not-found error, and single-file skill

## 5. art cat

- [x] 5.1 Add `cat` parser to the top-level `art` subparsers with `artifact` positional, `-V`/`--vault`, `--here`, and `--tools` flags
- [x] 5.2 Implement `handle_cat`: resolve artifact using existing resolution logic; for skills print `SKILL.md` content; for commands/agents print the `.md` file content
- [x] 5.3 Implement sub-path support in `handle_cat` using the same `[type/]name[/sub/path]` parsing (task 1.3); error on sub-path for file-based artifacts
- [x] 5.4 Support frontmatter name fallback in artifact resolution for `art cat`
- [x] 5.5 Register `cat` in the main command dispatch in `_main()` / `main()`
- [x] 5.6 Write tests for `art cat` including skill, command, agent, sub-path, not-found, and file-based sub-path error

## 6. art inspect

- [x] 6.1 Add `inspect` parser to the top-level `art` subparsers with `artifact` positional, `-V`/`--vault`, `--here`, and `--tools` flags
- [x] 6.2 Implement `handle_inspect`: resolve artifact; parse YAML frontmatter from primary file; display as indented key-value pairs under a "Frontmatter" header
- [x] 6.3 For directory-based artifacts, add a "Files" section listing the file tree (SKILL.md first with `(main)` label, then remaining files with relative paths)
- [x] 6.4 Support frontmatter name fallback in artifact resolution for `art inspect`
- [x] 6.5 Register `inspect` in the main command dispatch
- [x] 6.6 Write tests for `art inspect` including frontmatter display, file tree, file-based artifact (no file tree), and not-found

## 7. art export

- [x] 7.1 Add `export` parser to the top-level `art` subparsers with `artifact` positional, `-V`/`--vault`, and `-o`/`--output` flags
- [x] 7.2 Implement `handle_export`: resolve artifact; determine zip output path (default: `<cwd>/<artifact-name>.zip`); error if output path already exists
- [x] 7.3 For skill artifacts: zip all files under `<artifact-dir>/` into `<artifact-name>/` at zip root
- [x] 7.4 For command/agent artifacts: zip the `.md` file as `<artifact-name>/<artifact-name>.md`
- [x] 7.5 Support `[type/]name` prefix syntax and frontmatter name fallback for `art export`
- [x] 7.6 Register `export` in the main command dispatch
- [x] 7.7 Write tests for `art export` including skill (with subdirs), command, output path collision, not-found, and zip internal structure

## 8. art store — Zip Input Support

- [x] 8.1 Update `handle_store` to detect when `target_dir` ends with `.zip`: run zip detection and extraction before normal store flow
- [x] 8.2 Implement `_detect_zip_artifact_type(extracted_dir: Path) -> str`: inspect root entries to classify as `single-skill`, `single-file-artifact`, or `vault-bundle`
- [x] 8.3 For `single-skill` and `single-file-artifact`: skip the artifact selection modal, store the artifact directly
- [x] 8.4 For `vault-bundle`: pass extracted directory to the existing selection modal flow
- [x] 8.5 Extract zip to `tempfile.mkdtemp()` and ensure cleanup via try/finally on success and failure
- [x] 8.6 Error if zip file does not exist, is not a valid zip, or contains no recognizable artifact structure
- [x] 8.7 Error if zip target is combined with `--global` flag
- [x] 8.8 Write tests for zip detection heuristics (single skill, single command, vault bundle, invalid zip, empty zip)

## 9. Tests and Integration

- [x] 9.1 Run the full test suite (`pytest`) and fix any regressions from parser refactoring (especially `art edit` backward compatibility)
- [x] 9.2 Verify `art edit skill my-skill` (old form) and `art edit my-skill` (new form) both work end-to-end
- [x] 9.3 Verify `art ls`, `art cat`, `art inspect`, `art export` appear correctly in `art --help`
- [x] 9.4 Update `README.md` under the "Extended Usage" heading to document new commands and flags
