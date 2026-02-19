## ADDED Requirements

### Requirement: art edit accepts a unified artifact specifier with optional type prefix
`art edit` MUST accept a single positional argument in the form `[type/]name[/sub/path]` in addition to the existing two-positional form (`type name`), enabling type auto-detection and sub-path targeting.

#### Scenario: Auto-detect type from artifact name
- **WHEN** `art edit my-skill` is run and exactly one artifact named `my-skill` is found across all types in the target vault
- **THEN** the artifact MUST be edited without requiring an explicit type argument

#### Scenario: Ambiguous name requires type prefix
- **WHEN** `art edit my-artifact` is run and artifacts named `my-artifact` exist under more than one type in the target vault
- **THEN** an error MUST be printed to stderr listing the ambiguous matches and instructing the user to use a type prefix (e.g. `skill/my-artifact`)

#### Scenario: Type prefix resolves ambiguity
- **WHEN** `art edit skill/my-artifact` is run
- **THEN** the skill named `my-artifact` MUST be edited, regardless of whether other artifact types share the same name

#### Scenario: Short type aliases work as prefix
- **WHEN** `art edit s/my-skill`, `art edit sk/my-skill`, `art edit c/my-command`, `art edit cmd/my-command`, `art edit a/my-agent`, `art edit agt/my-agent` is run
- **THEN** each MUST resolve the artifact of the indicated type

#### Scenario: Old two-positional form still works
- **WHEN** `art edit skill my-skill` is run (two separate positional arguments)
- **THEN** the skill named `my-skill` MUST be edited (backward-compatible behavior)

#### Scenario: Artifact not found
- **WHEN** `art edit nonexistent` is run and no artifact by that name or frontmatter name is found
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

### Requirement: art edit -i / --interactive flag forces the picker
A new `-i` / `--interactive` flag MUST be supported on `art edit` to force the interactive file picker for directory-based artifacts.

#### Scenario: -i forces picker even for single-file skills
- **WHEN** `art edit my-skill -i` is run and the skill contains only `SKILL.md`
- **THEN** the interactive picker MUST be displayed

#### Scenario: -i on file-based artifact is a no-op
- **WHEN** `art edit my-command -i` is run
- **THEN** `my-command.md` MUST be opened in `$EDITOR` and the `-i` flag MUST have no effect

### Requirement: art edit -m / --main flag skips picker
A new `-m` / `--main` flag MUST be supported on `art edit` to bypass the interactive picker and open the primary file directly.

#### Scenario: -m bypasses picker for multi-file skill
- **WHEN** `art edit my-skill -m` is run and the skill contains multiple files
- **THEN** `SKILL.md` MUST be opened in `$EDITOR` without showing the picker

### Requirement: art edit -n / --new-file flag creates a file within a directory-based artifact
A new `-n` / `--new-file` flag MUST be supported on `art edit` to create a new file at a given relative path within a directory-based artifact and open it in the editor.

#### Scenario: New file created within skill
- **WHEN** `art edit my-skill -n references/new-ref.md` is run
- **THEN** `<skill-dir>/references/new-ref.md` MUST be created (including intermediate directories) and opened in `$EDITOR`

#### Scenario: -n on file-based artifact errors
- **WHEN** `art edit my-command -n some-file.md` is run
- **THEN** an error MUST be printed to stderr stating `--new-file` is not supported for file-based artifact types

#### Scenario: -n with path that already exists errors
- **WHEN** `art edit my-skill -n references/existing.md` is run and that file already exists
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1
