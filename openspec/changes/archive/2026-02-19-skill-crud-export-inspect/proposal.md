## Why

Skills are directory-based artifacts that can contain many files (`references/`, `templates/`, etc.), but the current tooling treats them as single-file artifacts — `art edit skill <name>` opens only `SKILL.md`, and there is no way to list, create, import, or delete files within a skill from the CLI. Additionally, there is no way to view artifact content inline, inspect artifact metadata without opening an editor, or export individual artifacts as portable zip files for sharing.

## What Changes

- `art edit` gains auto-type-detection (type inferred from name, with `type/name` prefix for disambiguation), sub-path support (`art edit my-skill/references/hooks.md`), and an interactive file picker for directory-based artifacts (skills) with create/import/delete actions
- `art ls` gains an optional artifact-name positional argument to list files within a directory-based artifact
- `art cat` is introduced as a new command that prints the primary file content of any artifact (or a specific sub-path file for skills)
- `art inspect` is introduced as a new command that displays structured frontmatter metadata and the directory tree for directory-based artifacts
- `art export` is introduced as a new command that exports a single artifact as a `.zip` archive, supporting the same `[type/]name` prefix syntax as other commands
- `art store` gains the ability to accept a `.zip` file as its target, auto-detecting whether the zip contains a single artifact or a vault bundle and adapting accordingly

## Capabilities

### New Capabilities
- `skill-file-management`: Interactive file picker for directory-based artifacts in `art edit`; sub-path targeting for editing, creating, importing, and deleting files within a skill's directory
- `artifact-cat`: New `art cat` command that prints the content of an artifact's primary file, with optional slash-delimited sub-path for non-primary files in directory-based artifacts
- `artifact-inspect`: New `art inspect` command that displays parsed YAML frontmatter fields and (for directory-based artifacts) a file tree of all files within the artifact directory
- `artifact-export`: New `art export` command that packages a single artifact as a `.zip` archive with the artifact's directory structure preserved, using standard `[type/]name` prefix syntax
- `artifact-store-zip`: Extension to `art store` to accept a `.zip` file path as target, auto-detecting single-artifact zips (store directly) vs vault bundle zips (show selection modal)

### Modified Capabilities
- `artifact-editing`: `art edit` type argument becomes optional; type is auto-detected when omitted, with `type/name` prefix for disambiguation; sub-path added as suffix after artifact name (`name/sub/path`)
- `vault-artifact-listing`: `art ls` accepts an optional artifact-name positional argument; when provided and artifact is directory-based, lists files within that artifact's directory; errors if artifact is file-based

## Impact

- `cli.py`: `handle_edit` refactored for auto-detection, sub-path resolution, and interactive picker; `handle_list` extended for artifact sub-path listing; new `handle_cat`, `handle_inspect`, `handle_export` handlers; `handle_store` extended for zip input
- `creator.py`: New `resolve_edit_target` variant or extension to support sub-path resolution and artifact type auto-detection
- New interactive picker utility (inline in `cli.py` or extracted): renders skill file tree with keyboard navigation and action options (open, new file, import file, delete file)
- No new external dependencies: zip via stdlib `zipfile`, temp dirs via stdlib `tempfile`, interactive input via stdlib `sys.stdin`
