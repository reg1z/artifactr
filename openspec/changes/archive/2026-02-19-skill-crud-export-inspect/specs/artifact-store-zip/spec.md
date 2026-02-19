## ADDED Requirements

### Requirement: art store accepts a zip file as its target
The `art store` command MUST accept a `.zip` file path as its `target_dir` argument and auto-detect whether the zip contains a single artifact or a vault bundle.

#### Scenario: Single-skill zip auto-stores without selection modal
- **WHEN** `art store ./my-skill.zip` is run and the zip contains a single directory with `SKILL.md`
- **THEN** the skill MUST be stored directly into the target vault without displaying the artifact selection modal

#### Scenario: Single command/agent zip auto-stores without selection modal
- **WHEN** `art store ./my-command.zip` is run and the zip contains a single directory with one `.md` file
- **THEN** the artifact MUST be stored directly into the target vault without displaying the artifact selection modal

#### Scenario: Vault bundle zip shows selection modal
- **WHEN** `art store ./bundle.zip` is run and the zip contains multiple root directories or root-level `skills/`/`commands/`/`agents/` subdirectories
- **THEN** the artifact selection modal MUST be displayed, allowing the user to select which artifacts to store

#### Scenario: Zip file extracted to temp directory
- **WHEN** a zip file is provided as the target
- **THEN** the zip MUST be extracted to a platform-appropriate temporary directory (via `tempfile.mkdtemp()`)
- **AND** the temp directory MUST be deleted after the store operation completes (success or failure)

#### Scenario: Zip file does not exist
- **WHEN** `art store ./nonexistent.zip` is run and the file does not exist
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

#### Scenario: File is not a valid zip
- **WHEN** `art store ./file.zip` is run and the file is not a valid zip archive
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

#### Scenario: Empty zip archive
- **WHEN** the zip file contains no recognizable artifact structure
- **THEN** an error MUST be printed to stderr describing that no artifacts were found in the zip

### Requirement: art store zip detection uses content inspection
Zip type detection MUST be based on the internal structure of the archive, not any manifest or metadata file.

#### Scenario: Single artifact detection heuristic
- **WHEN** the zip contains exactly one root-level directory and that directory contains `SKILL.md`
- **THEN** it MUST be classified as a single skill artifact

#### Scenario: Single file-based artifact detection heuristic
- **WHEN** the zip contains exactly one root-level directory and that directory contains a single `.md` file matching the directory name
- **THEN** it MUST be classified as a single command or agent artifact (type inferred by attempting to parse frontmatter `type` field; defaults to command if absent)

#### Scenario: Vault bundle detection heuristic
- **WHEN** the zip root contains multiple directories, OR a single directory that itself contains `skills/`, `commands/`, or `agents/` subdirectories
- **THEN** it MUST be classified as a vault bundle and the selection modal MUST be shown

### Requirement: art store zip target is mutually exclusive with --global
A zip file path MUST NOT be used together with the `--global` flag.

#### Scenario: Zip with --global errors
- **WHEN** `art store ./my-skill.zip --global` is run
- **THEN** an error MUST be printed to stderr stating that a zip file target and `--global` cannot be used together
