## ADDED Requirements

### Requirement: Link command in project namespace
`art proj link` MUST convert copied artifacts to symlinks pointing to the vault source. Aliases: `ln`.

#### Scenario: Link specific artifact by name
- **WHEN** `art proj link helping-hand` is run
- **THEN** the imported artifact `helping-hand` from the default vault MUST be replaced with a symlink to its vault source
- **AND** the `.art-cache/imported` entry MUST be updated to `:linked`
- **AND** artifacts with the same name from other vaults MUST NOT be affected

#### Scenario: Link multiple artifacts by name
- **WHEN** `art proj link helping-hand code-review` is run
- **THEN** each named artifact MUST be converted to a symlink

#### Scenario: Link all artifacts from default vault
- **WHEN** `art proj link --all` is run
- **THEN** all imported copied artifacts from the default vault MUST be converted to symlinks
- **AND** artifacts imported from other vaults MUST NOT be affected

#### Scenario: Link all artifacts from specific vault
- **WHEN** `art proj link --all -V other-vault` is run
- **THEN** all imported copied artifacts from `other-vault` MUST be converted to symlinks
- **AND** artifacts imported from other vaults MUST NOT be affected

#### Scenario: Link all artifacts from multiple vaults
- **WHEN** `art proj link --all -V vault1,vault2` or `art proj link --all -V vault1 -V vault2` is run
- **THEN** all imported copied artifacts from both `vault1` and `vault2` MUST be converted to symlinks

#### Scenario: Link without arguments or --all
- **WHEN** `art proj link` is run without artifact names and without `--all`
- **THEN** an error MUST be displayed: "Specify artifact names or use --all/-a to link all artifacts."

#### Scenario: Link with glob pattern
- **WHEN** `art proj link "skill-*"` is run
- **THEN** all imported artifacts whose names match the glob pattern MUST be converted to symlinks

#### Scenario: Link artifact that is already linked
- **WHEN** `art proj link helping-hand` is run and the artifact is already a symlink
- **THEN** the operation MUST be skipped with a message indicating the artifact is already linked

#### Scenario: Link alias
- **WHEN** `art proj ln helping-hand` is run
- **THEN** it MUST behave identically to `art proj link helping-hand`

### Requirement: Unlink command in project namespace
`art proj unlink` MUST convert symlinked artifacts to independent copies. Aliases: `uln`.

#### Scenario: Unlink specific artifact by name
- **WHEN** `art proj unlink helping-hand` is run
- **THEN** the symlinked artifact MUST be replaced with a copy of the file content
- **AND** the `.art-cache/imported` entry MUST be updated to `:copied`

#### Scenario: Unlink multiple artifacts by name
- **WHEN** `art proj unlink helping-hand code-review` is run
- **THEN** each named artifact MUST be converted to a copy

#### Scenario: Unlink all artifacts from default vault
- **WHEN** `art proj unlink --all` is run
- **THEN** all imported linked artifacts from the default vault MUST be converted to copies
- **AND** artifacts imported from other vaults MUST NOT be affected

#### Scenario: Unlink all artifacts from specific vault
- **WHEN** `art proj unlink --all -V other-vault` is run
- **THEN** all imported linked artifacts from `other-vault` MUST be converted to copies

#### Scenario: Unlink without arguments or --all
- **WHEN** `art proj unlink` is run without artifact names and without `--all`
- **THEN** an error MUST be displayed: "Specify artifact names or use --all/-a to unlink all artifacts."

#### Scenario: Unlink with glob pattern
- **WHEN** `art proj unlink "code-*"` is run
- **THEN** all imported artifacts whose names match the glob pattern MUST be converted to copies

#### Scenario: Unlink artifact that is already copied
- **WHEN** `art proj unlink helping-hand` is run and the artifact is already a copy
- **THEN** the operation MUST be skipped with a message indicating the artifact is already a copy

#### Scenario: Unlink alias
- **WHEN** `art proj uln helping-hand` is run
- **THEN** it MUST behave identically to `art proj unlink helping-hand`

### Requirement: Link command in config namespace
`art conf link` MUST convert copied global artifacts to symlinks. Aliases: `ln`.

#### Scenario: Link specific global artifact
- **WHEN** `art conf link helping-hand` is run
- **THEN** the globally imported artifact MUST be replaced with a symlink to its vault source
- **AND** the global `.art-cache-global/imported` entry MUST be updated to `:linked`

#### Scenario: Link all global artifacts from default vault
- **WHEN** `art conf link --all` is run
- **THEN** all globally imported copied artifacts from the default vault MUST be converted to symlinks
- **AND** artifacts imported from other vaults MUST NOT be affected

#### Scenario: Link alias in config
- **WHEN** `art conf ln -a` is run
- **THEN** it MUST behave identically to `art conf link --all`

### Requirement: Unlink command in config namespace
`art conf unlink` MUST convert symlinked global artifacts to copies. Aliases: `uln`.

#### Scenario: Unlink specific global artifact
- **WHEN** `art conf unlink helping-hand` is run
- **THEN** the globally imported symlinked artifact MUST be replaced with a copy
- **AND** the global `.art-cache-global/imported` entry MUST be updated to `:copied`

#### Scenario: Unlink all global artifacts from default vault
- **WHEN** `art conf unlink --all` is run
- **THEN** all globally imported linked artifacts from the default vault MUST be converted to copies
- **AND** artifacts imported from other vaults MUST NOT be affected

#### Scenario: Unlink alias in config
- **WHEN** `art conf uln helping-hand` is run
- **THEN** it MUST behave identically to `art conf unlink helping-hand`

### Requirement: Diff detection on link
When `link` replaces a local copy with a symlink, the system MUST detect if the local copy differs from the vault version.

#### Scenario: Local copy matches vault
- **WHEN** `art proj link helping-hand` is run and the local copy is identical to the vault file
- **THEN** the copy MUST be replaced with a symlink without prompting

#### Scenario: Local copy differs from vault
- **WHEN** `art proj link helping-hand` is run and the local copy differs from the vault file
- **THEN** the user MUST be prompted with options: `[b]ackup and link / [s]kip / [l]ink anyway`

#### Scenario: User selects backup
- **WHEN** the user selects `b` at the diff prompt
- **THEN** the local copy MUST be saved to `.art-cache/backups/YYYY-MM-DD/<artifact_type>/<artifact_name>/`
- **AND** the copy MUST be replaced with a symlink

#### Scenario: User selects skip
- **WHEN** the user selects `s` at the diff prompt
- **THEN** the artifact MUST be left unchanged

#### Scenario: User selects link anyway
- **WHEN** the user selects `l` at the diff prompt
- **THEN** the copy MUST be replaced with a symlink without backing up

#### Scenario: Force flag auto-backups
- **WHEN** `art proj link helping-hand -f` is run and the local copy differs
- **THEN** the local copy MUST be automatically backed up and replaced with a symlink without prompting

### Requirement: Backup storage
Backups MUST be stored under `.art-cache/backups/` organized by date and artifact type.

#### Scenario: Backup directory structure
- **WHEN** an artifact backup is created
- **THEN** it MUST be stored at `.art-cache/backups/YYYY-MM-DD/<artifact_type>/<artifact_name>/`

#### Scenario: Same-day backup overwrite
- **WHEN** the same artifact is backed up twice on the same day
- **THEN** the second backup MUST overwrite the first

#### Scenario: Backup preserves content
- **WHEN** a file artifact is backed up
- **THEN** the backup MUST contain an exact copy of the file content

#### Scenario: Backup preserves directory structure
- **WHEN** a directory artifact (e.g., a skill with multiple files) is backed up
- **THEN** the entire directory structure and all files MUST be preserved in the backup

### Requirement: Glob pattern matching for artifact names
Link and unlink commands MUST support glob patterns for targeting artifacts.

#### Scenario: Wildcard pattern
- **WHEN** `art proj link "skill-*"` is run
- **THEN** all imported artifacts whose names match `skill-*` via `fnmatch` MUST be targeted

#### Scenario: Question mark pattern
- **WHEN** `art proj unlink "skill-?"` is run
- **THEN** all imported artifacts whose names match `skill-?` via `fnmatch` MUST be targeted

#### Scenario: No matches
- **WHEN** a glob pattern matches no imported artifacts
- **THEN** a message MUST be displayed indicating no artifacts matched the pattern

#### Scenario: Mixed names and patterns
- **WHEN** `art proj link helping-hand "code-*"` is run
- **THEN** both the exact name and the glob pattern MUST be resolved against imported artifacts

### Requirement: Inode-based hard link detection
An `are_hardlinked()` utility function MUST exist to detect if two files are hard links to the same data.

#### Scenario: Same inode on same device
- **WHEN** `are_hardlinked(file_a, file_b)` is called and both files share the same `st_dev` and `st_ino`
- **THEN** it MUST return `True`

#### Scenario: Different files
- **WHEN** `are_hardlinked(file_a, file_b)` is called and the files have different inodes
- **THEN** it MUST return `False`

#### Scenario: Cross-platform compatibility
- **WHEN** `are_hardlinked()` is called on Windows
- **THEN** it MUST work using NTFS file index values from `os.stat()`
