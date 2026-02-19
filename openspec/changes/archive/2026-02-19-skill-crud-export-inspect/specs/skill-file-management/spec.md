## ADDED Requirements

### Requirement: Interactive file picker for directory-based artifacts
When `art edit` resolves a directory-based artifact (currently: skills) and no sub-path is specified, the system MUST display an interactive numbered file picker showing the artifact's file tree.

#### Scenario: Picker shown when skill has files beyond SKILL.md
- **WHEN** `art edit my-skill` is run and `my-skill/` contains files other than `SKILL.md`
- **THEN** the interactive picker MUST be displayed showing all files in the skill directory
- **AND** the user MUST be prompted to select a file or action

#### Scenario: Picker skipped when skill has only SKILL.md
- **WHEN** `art edit my-skill` is run and `my-skill/` contains only `SKILL.md`
- **THEN** `SKILL.md` MUST be opened directly in `$EDITOR` without showing the picker

#### Scenario: Force picker with -i / --interactive
- **WHEN** `art edit my-skill -i` or `art edit my-skill --interactive` is run
- **THEN** the picker MUST always be shown, even if the skill contains only `SKILL.md`

#### Scenario: Skip picker with -m / --main
- **WHEN** `art edit my-skill -m` or `art edit my-skill --main` is run
- **THEN** `SKILL.md` MUST be opened directly in `$EDITOR` without showing the picker, regardless of how many files the skill contains

#### Scenario: Picker not shown for non-TTY stdin
- **WHEN** `art edit my-skill` is run and `sys.stdin.isatty()` returns `False`
- **THEN** the picker MUST NOT be displayed; the primary file (SKILL.md) MUST be opened directly

### Requirement: Picker displays skill file tree with numbered entries
The picker MUST render the artifact's file tree as a numbered list with action options.

#### Scenario: File tree rendering
- **WHEN** the picker is shown for a skill with nested files
- **THEN** all files within the skill directory MUST be listed with 1-based indices
- **AND** files in subdirectories MUST be shown with their relative path (e.g. `references/hooks.md`)
- **AND** `SKILL.md` MUST be listed first and labeled as `(main)`
- **AND** available actions MUST be displayed: `[n] New file`, `[d] Delete file`, `[i] Import file`, `[q] Quit`
- **AND** pressing Enter with no input MUST open `SKILL.md`

#### Scenario: Selecting a file by number opens it in editor
- **WHEN** the user enters a valid file index number
- **THEN** the corresponding file MUST be opened in `$EDITOR`

#### Scenario: Invalid index is rejected
- **WHEN** the user enters a number outside the valid range
- **THEN** an error message MUST be displayed and the prompt MUST be re-shown

### Requirement: Picker new-file action creates a file within the skill
When the user selects the new-file action in the picker, the system MUST prompt for a relative path and create the file.

#### Scenario: New file created at relative path
- **WHEN** the user selects `[n]` in the picker and enters `references/new-ref.md`
- **THEN** the file MUST be created at `<skill-dir>/references/new-ref.md`
- **AND** any intermediate directories MUST be created
- **AND** the new file MUST be opened in `$EDITOR`

#### Scenario: New file path collision
- **WHEN** the user enters a relative path that already exists within the skill directory
- **THEN** an error MUST be displayed and the file MUST NOT be overwritten

### Requirement: Picker import-file action copies an external file into the skill
When the user selects the import action in the picker, the system MUST prompt for a source path and copy it into the skill directory.

#### Scenario: File imported from filesystem path
- **WHEN** the user selects `[i]` in the picker and enters an absolute or `~`-expanded path to an existing file
- **THEN** the file MUST be copied into the skill directory
- **AND** the user MUST be prompted for an optional destination relative path within the skill (default: filename only, placed at skill root)
- **AND** the copied file MUST be opened in `$EDITOR`

#### Scenario: Import source path does not exist
- **WHEN** the user provides a source path that does not exist
- **THEN** an error MUST be displayed and no file MUST be created

#### Scenario: Import destination collision prompts for confirmation
- **WHEN** the destination path within the skill already exists
- **THEN** the user MUST be asked to confirm overwrite before the file is copied

### Requirement: Picker delete action removes a file from the skill
When the user selects the delete action in the picker, the system MUST prompt for a file to delete and confirm before removal.

#### Scenario: File selected for deletion
- **WHEN** the user selects `[d]` in the picker
- **THEN** the file tree MUST be re-displayed for selection
- **AND** after the user selects a file index, a confirmation prompt MUST be shown before deletion

#### Scenario: SKILL.md cannot be deleted via picker
- **WHEN** the user attempts to delete `SKILL.md` via the picker
- **THEN** an error MUST be displayed stating that the primary file cannot be deleted
- **AND** the picker MUST remain open

#### Scenario: File deleted successfully
- **WHEN** the user confirms deletion of a non-primary file
- **THEN** the file MUST be removed from disk
- **AND** any now-empty parent directories within the skill (except the skill root) MUST also be removed

### Requirement: Sub-path argument opens a specific file within a skill
`art edit` MUST accept a slash-delimited sub-path as part of the artifact specifier to directly open a file within a directory-based artifact.

#### Scenario: Sub-path opens specific file
- **WHEN** `art edit my-skill/references/hooks.md` is run
- **THEN** `<skill-dir>/references/hooks.md` MUST be opened in `$EDITOR`
- **AND** the picker MUST NOT be shown

#### Scenario: Sub-path with type prefix
- **WHEN** `art edit skill/my-skill/references/hooks.md` or `art edit sk/my-skill/references/hooks.md` is run
- **THEN** `<skill-dir>/references/hooks.md` MUST be opened in `$EDITOR`

#### Scenario: Sub-path file does not exist — error
- **WHEN** `art edit my-skill/nonexistent.md` is run and the file does not exist within the skill directory
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

#### Scenario: Sub-path used with -n / --new-file creates and opens file
- **WHEN** `art edit my-skill -n references/new.md` is run
- **THEN** `<skill-dir>/references/new.md` MUST be created (including intermediate directories) and opened in `$EDITOR`
- **AND** if the file already exists, an error MUST be printed to stderr and the command MUST exit with code 1

#### Scenario: Sub-path on file-based artifact errors
- **WHEN** `art edit my-command/some-file.md` is run and `my-command` is a command (file-based)
- **THEN** an error MUST be printed to stderr stating sub-paths are not supported for file-based artifact types
